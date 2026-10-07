# -*- coding: utf-8 -*-
"""知识库管理接口（仅管理员；整个路由统一做管理员鉴权）"""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import AppException
from ..database import get_db
from ..deps import require_admin
from ..models import Chunk, Document, KnowledgeBase
from ..schemas.admin import KbCreate, KbOut, KbUpdate
from ..services.ingestion_service import bump_content_version
from ..services.queue_worker import enqueue
from ..services.vectorstore import delete_where

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/kb",
    tags=["知识库管理"],
    dependencies=[Depends(require_admin)],  # 双保险：每个接口都要求管理员身份
)


def _get_kb_or_404(db: Session, kb_id: int) -> KnowledgeBase:
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise AppException("知识库不存在", 404)
    return kb


def _fill_counts(db: Session, kb: KnowledgeBase) -> KbOut:
    item = KbOut.model_validate(kb)
    item.document_count = (
        db.scalar(select(func.count()).select_from(Document).where(Document.kb_id == kb.id)) or 0
    )
    item.chunk_count = (
        db.scalar(select(func.count()).select_from(Chunk).where(Chunk.kb_id == kb.id)) or 0
    )
    return item


@router.get("", summary="知识库列表")
def list_kbs(db: Session = Depends(get_db)):
    kbs = db.scalars(select(KnowledgeBase).order_by(KnowledgeBase.created_at)).all()
    return [_fill_counts(db, kb) for kb in kbs]


@router.post("", summary="新建知识库")
def create_kb(payload: KbCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(KnowledgeBase).where(KnowledgeBase.name == payload.name))
    if exists:
        raise AppException("同名知识库已存在")
    kb = KnowledgeBase(name=payload.name, description=payload.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    logger.info("新建知识库：%s", kb.name)
    return _fill_counts(db, kb)


@router.patch("/{kb_id}", summary="修改知识库名称/描述")
def update_kb(kb_id: int, payload: KbUpdate, db: Session = Depends(get_db)):
    kb = _get_kb_or_404(db, kb_id)
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise AppException("知识库名称不能为空")
        dup = db.scalar(
            select(KnowledgeBase).where(KnowledgeBase.name == name, KnowledgeBase.id != kb_id)
        )
        if dup:
            raise AppException("同名知识库已存在")
        kb.name = name
    if payload.description is not None:
        kb.description = payload.description.strip()
    db.commit()
    db.refresh(kb)
    return _fill_counts(db, kb)


@router.delete("/{kb_id}", summary="删除知识库（连同全部文档和数据）")
def delete_kb(kb_id: int, db: Session = Depends(get_db)):
    kb = _get_kb_or_404(db, kb_id)

    # 1. 删向量库里的所有相关"数字 DNA"
    delete_where({"kb_id": kb_id})

    # 2. 删上传的原文件
    docs = db.scalars(select(Document).where(Document.kb_id == kb_id)).all()
    for doc in docs:
        p = Path(doc.file_path)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                logger.warning("删除原文件失败：%s", p)

    # 3. 删数据库记录（先删片段和文档，再删知识库）
    db.query(Chunk).filter(Chunk.kb_id == kb_id).delete()
    db.query(Document).filter(Document.kb_id == kb_id).delete()
    db.delete(kb)
    db.commit()
    bump_content_version(db)  # 内容变了，作废旧问答缓存
    logger.info("已删除知识库：%s（含 %s 份文档）", kb.name, len(docs))
    return {"message": f"知识库已删除（同时清除了 {len(docs)} 份文档的数据）"}


@router.post("/{kb_id}/reindex", summary="整库重建索引")
def reindex_kb(kb_id: int, db: Session = Depends(get_db)):
    kb = _get_kb_or_404(db, kb_id)
    docs = db.scalars(select(Document).where(Document.kb_id == kb_id)).all()
    for doc in docs:
        doc.status = "pending"
        doc.processed_chunks = 0
        doc.error_msg = None
        enqueue(doc.id)
    db.commit()
    logger.info("知识库 %s 重建索引：%s 份文档已入队", kb.name, len(docs))
    return {"message": f"已把 {len(docs)} 份文档加入重建队列，处理进度见文档列表"}
