# -*- coding: utf-8 -*-
r"""
入库流水线 —— 一份文档从"文件"变成"可被检索的知识"的全过程

流程（每一步都会更新进度，前端能看到）：
  1. 解析：把 pdf/word/excel 等读成纯文字
  2. 清洗：去掉乱码、多余空行
  3. 分块：切成约 500 字的小段（相邻段留 50 字重叠，避免一句话被拦腰切断）
  4. 每段开头加上「【文档：文件名】」——让 AI 回答时知道这段话来自哪份资料
  5. 存 SQLite（文字正本）+ 分批写入 Chroma（数字 DNA）
  6. 全部完成 → 状态改为"已完成"；中途出错 → 状态改为"失败"（带中文原因）

由 queue_worker.py 的单线程队列调用（一次只处理一份文档，不抢显存、不卡界面）。
"""
import logging
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select

from ..config import settings
from ..core.exceptions import AppException
from ..database import SessionLocal
from ..models import Chunk, Document, Meta
from ..utils.file_parsers import parse_file
from ..utils.text_cleaning import clean_text

logger = logging.getLogger(__name__)

# 中文友好的分块分隔符优先级（先按段落切，再按句子切，最后按字切）
_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    length_function=len,
)

_VECTOR_BATCH = 100  # 每向量化 100 条更新一次进度


def bump_content_version(db) -> None:
    """全局内容版本 +1：让所有旧的问答缓存自动作废（内容变了，旧答案不可信了）"""
    row = db.get(Meta, "content_version")
    if row is None:
        db.add(Meta(key="content_version", value="1"))
    else:
        row.value = str(int(row.value or "0") + 1)
    db.commit()


def get_content_version(db) -> int:
    row = db.get(Meta, "content_version")
    return int(row.value) if row and row.value else 0


def process_document(document_id: int) -> None:
    """完整处理一份文档（本函数由队列 worker 调用，不直接暴露给接口）"""
    db = SessionLocal()
    doc: Document | None = None
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("文档 %s 不存在，跳过", document_id)
            return
        if doc.status == "ready":
            return

        _set_status(db, doc, "processing")
        logger.info("开始处理文档：%s（%s）", doc.filename, doc.file_type)

        # 1~2. 解析 + 清洗
        raw_text = parse_file(Path(doc.file_path), doc.file_type)
        text = clean_text(raw_text)

        # 3. 分块
        pieces = _SPLITTER.split_text(text)
        pieces = [p.strip() for p in pieces if p.strip()]
        if not pieces:
            raise AppException("文档切分后没有任何内容，请检查文件")

        # 4~5a. 写 SQLite（先清掉旧数据，重建索引时不会重复）
        _clear_existing(db, doc)
        header = f"【文档：{doc.filename}】\n"
        db.add_all(
            Chunk(
                document_id=doc.id,
                kb_id=doc.kb_id,
                chunk_index=i,
                content=header + piece,
                char_count=len(header) + len(piece),
            )
            for i, piece in enumerate(pieces)
        )
        doc.chunk_count = len(pieces)
        doc.processed_chunks = 0
        db.commit()

        # 取回带 id 的记录（向量库 metadata 需要引用 chunk id）
        rows = db.scalars(
            select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.chunk_index)
        ).all()

        # 5b. 分批向量化 → 写 Chroma（每批更新进度条）
        from .vectorstore import add_texts  # 延迟导入：避免启动时加载模型

        for start in range(0, len(rows), _VECTOR_BATCH):
            batch = rows[start : start + _VECTOR_BATCH]
            add_texts(
                ids=[f"c{r.id}" for r in batch],
                texts=[r.content for r in batch],
                metadatas=[
                    {"chunk_id": r.id, "document_id": doc.id, "kb_id": doc.kb_id}
                    for r in batch
                ],
            )
            doc.processed_chunks = min(start + _VECTOR_BATCH, len(rows))
            db.commit()

        # 6. 完成
        _set_status(db, doc, "ready")
        doc.error_msg = None
        db.commit()
        bump_content_version(db)
        logger.info("文档处理完成：%s（%s 段）", doc.filename, doc.chunk_count)

    except Exception as exc:  # noqa: BLE001 —— 任何失败都要落库，让用户看到原因
        db.rollback()
        logger.exception("文档处理失败：%s", document_id)
        if doc is not None:
            doc = db.get(Document, document_id)
            if doc is not None:
                doc.status = "failed"
                doc.error_msg = (
                    str(exc) if isinstance(exc, AppException) else f"处理失败：{exc}"
                )
                db.commit()
    finally:
        db.close()


def _set_status(db, doc: Document, status: str) -> None:
    doc.status = status
    db.commit()


def _clear_existing(db, doc: Document) -> None:
    """清掉这份文档旧的片段和向量（重建索引/重试时先清后建）"""
    old_chunks = db.scalars(select(Chunk).where(Chunk.document_id == doc.id)).all()
    if old_chunks:
        for row in old_chunks:
            db.delete(row)
        db.commit()
    from .vectorstore import delete_where  # 延迟导入

    delete_where({"document_id": doc.id})


def delete_document_data(db, doc: Document) -> None:
    """删除一份文档的全部数据：向量 → 片段 → 原文件（供删除接口调用）"""
    from .vectorstore import delete_where

    delete_where({"document_id": doc.id})
    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
    file_path = Path(doc.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            logger.warning("删除原文件失败（不影响数据）：%s", file_path)
    db.delete(doc)
    db.commit()
    bump_content_version(db)
