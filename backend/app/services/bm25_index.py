# -*- coding: utf-8 -*-
"""
BM25 关键词检索 —— 与向量检索互补的"另一路人马"

打个比方：
  - 向量检索像"懂意思的图书管理员"：你说"能听多久"，他能找到"续航 30 小时"
  - BM25 像"精确查找的检索机"：你说"W1"或"8000Pa"，它一找一个准
两路人马的结果融合后，既懂意思又抓得住精确词。

实现要点：
  - 中文需要先"分词"（jieba 把句子切成词），然后按词匹配
  - 全部片段常驻内存（几万条以内毫无压力），知识库内容有变化时自动重建
"""
import logging
import threading

import jieba
from rank_bm25 import BM25Okapi
from sqlalchemy import select

from ..database import SessionLocal
from ..models import Chunk

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_index: dict | None = None  # {"bm25": 模型, "items": [片段数据], "version": 版本号}


def _build_index(version: int) -> dict:
    """从数据库读取全部片段，建立关键词索引（知识库变化后调用）"""
    db = SessionLocal()
    try:
        rows = db.scalars(select(Chunk).order_by(Chunk.id)).all()
        items = [
            {
                "chunk_id": r.id,
                "document_id": r.document_id,
                "kb_id": r.kb_id,
                "text": r.content,
            }
            for r in rows
        ]
    finally:
        db.close()

    # jieba 搜索引擎模式分词（切得更细，检索效果更好）
    corpus_tokens = [list(jieba.cut_for_search(it["text"])) for it in items]
    bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None
    logger.info("BM25 关键词索引构建完成：%s 个片段", len(items))
    return {"bm25": bm25, "items": items, "version": version}


def get_index(version: int) -> dict:
    """
    获取索引（带缓存）。

    version 是知识库的"内容版本号"：只要知识库有增删改，版本号就会变化，
    这里自动重建索引——保证关键词检索用的永远是最新内容。
    """
    global _index
    with _lock:
        if _index is None or _index["version"] != version:
            _index = _build_index(version)
        return _index


def search(question: str, top_k: int, version: int) -> list[dict]:
    """
    关键词检索。
    返回 [{chunk_id, document_id, kb_id, text, bm25_score}]（按分数从高到低）
    """
    idx = get_index(version)
    if idx["bm25"] is None:
        return []

    tokens = list(jieba.cut_for_search(question))
    scores = idx["bm25"].get_scores(tokens)

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    result: list[dict] = []
    for i in ranked:
        if scores[i] <= 0:  # 一个词都没对上的，不要
            break
        item = dict(idx["items"][i])
        item["bm25_score"] = float(scores[i])
        result.append(item)
    return result


def warm_up_async() -> None:
    """服务启动时后台预热（提前把索引建好，第一问不用等）"""
    def _warm():
        try:
            from .ingestion_service import get_content_version

            db = SessionLocal()
            try:
                version = get_content_version(db)
            finally:
                db.close()
            get_index(version)
            logger.info("BM25 关键词索引预热完成")
        except Exception:  # noqa: BLE001
            logger.exception("BM25 索引预热失败")

    threading.Thread(target=_warm, daemon=True, name="bm25-warmup").start()
