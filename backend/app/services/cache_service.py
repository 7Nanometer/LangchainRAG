# -*- coding: utf-8 -*-
"""
语义缓存 —— 问过的问题直接秒回（省钱 + 提速）

两种命中方式：
  1. 完全相同的问题（去掉空格标点后完全一样）→ 直接命中
  2. 意思相同的问题（问题向量相似度 ≥ 0.92）→ 向量比对命中
     （比如"耳机续航多久"和"W1 能听多长时间"）

安全机制：
  - 缓存带「内容版本号」：知识库资料一变化，旧缓存自动全部作废
    （避免用旧资料的回答来误导用户）
  - 缓存条数有上限（默认 5000），超出后优先淘汰"最少被用到"的
"""
import hashlib
import json
import logging
import re
import threading
from datetime import datetime

import numpy as np
from sqlalchemy import func, select

from ..config import settings
from ..database import SessionLocal
from ..models import QaCache

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_matrix_cache: dict | None = None  # {"ids": [...], "matrix": np.ndarray, "version": int}

_PUNCT_RE = re.compile(r"[\s，。？！、,.?!;；:：'\"“”‘’()（）\-—]+")


def normalize_question(q: str) -> str:
    """问题标准化：去掉空白和标点、统一小写（用于"完全相同"判断）"""
    return _PUNCT_RE.sub("", q).lower()


def question_hash(q: str) -> str:
    return hashlib.sha256(normalize_question(q).encode("utf-8")).hexdigest()[:32]


def find_cached(question: str, question_vector: list[float], version: int) -> dict | None:
    """查缓存；命中返回 {answer, citations, hit_count}，否则 None"""
    db = SessionLocal()
    try:
        # 1. 完全相同的问题
        row = db.scalar(select(QaCache).where(QaCache.question_hash == question_hash(question)))
        if row is not None and row.content_version == version:
            _touch(db, row)
            logger.info("缓存命中（完全相同）：%s", question[:30])
            return _to_result(row)

        # 2. 意思相似的问题（向量比对）
        hit_id = _similar_lookup(question_vector, version)
        if hit_id is not None:
            row = db.get(QaCache, hit_id)
            if row is not None and row.content_version == version:
                _touch(db, row)
                logger.info("缓存命中（相似）：%s ←→ %s", question[:30], row.question[:30])
                return _to_result(row)
        return None
    finally:
        db.close()


def save_cache(
    question: str,
    question_vector: list[float],
    answer: str,
    citations_json: str,
    version: int,
) -> None:
    """生成完成后写缓存（同一问题覆盖更新；超限时淘汰旧缓存）"""
    db = SessionLocal()
    try:
        qhash = question_hash(question)
        vec_bytes = np.asarray(question_vector, dtype=np.float32).tobytes()
        row = db.scalar(select(QaCache).where(QaCache.question_hash == qhash))
        if row is not None:
            row.question = question
            row.question_vector = vec_bytes
            row.answer = answer
            row.citations_json = citations_json
            row.content_version = version
            row.created_at = datetime.now()
        else:
            db.add(
                QaCache(
                    scope="all",
                    question=question,
                    question_hash=qhash,
                    question_vector=vec_bytes,
                    answer=answer,
                    citations_json=citations_json,
                    content_version=version,
                )
            )
            _evict_if_needed(db)
        db.commit()
        _invalidate_matrix()  # 有新缓存写入，矩阵下次重新加载
    except Exception:  # noqa: BLE001 —— 缓存失败不能影响正常回答
        db.rollback()
        logger.exception("写入问答缓存失败（不影响回答）")
    finally:
        db.close()


def _evict_if_needed(db) -> None:
    """缓存条数达到上限时，淘汰最不常用的 20%"""
    count = db.scalar(select(func.count()).select_from(QaCache)) or 0
    if count < settings.cache_max_entries:
        return
    victims = db.scalars(
        select(QaCache)
        .order_by(QaCache.hit_count.asc(), QaCache.created_at.asc())
        .limit(max(1, settings.cache_max_entries // 5))
    ).all()
    for v in victims:
        db.delete(v)
    logger.info("缓存超上限，已淘汰 %s 条不常用的旧缓存", len(victims))


def _touch(db, row: QaCache) -> None:
    """记录一次命中（用于统计和淘汰策略）"""
    row.hit_count = (row.hit_count or 0) + 1
    row.last_hit_at = datetime.now()
    db.commit()


def _to_result(row: QaCache) -> dict:
    try:
        citations = json.loads(row.citations_json or "[]")
    except (ValueError, TypeError):
        citations = []
    return {"answer": row.answer, "citations": citations, "hit_count": row.hit_count or 0}


def _invalidate_matrix() -> None:
    global _matrix_cache
    with _lock:
        _matrix_cache = None


def _similar_lookup(question_vector: list[float], version: int) -> int | None:
    """在缓存向量矩阵里找最相似的一条（相似度 ≥ 阈值才认）"""
    data = _get_matrix(version)
    if data is None or not data["ids"] or data["matrix"] is None:
        return None
    q = np.asarray(question_vector, dtype=np.float32)
    # BGE 向量已做归一化 → 点积 = 余弦相似度
    sims = data["matrix"] @ q
    best = int(np.argmax(sims))
    if float(sims[best]) >= settings.cache_similarity_threshold:
        return data["ids"][best]
    return None


def _get_matrix(version: int) -> dict | None:
    """加载当前版本的缓存向量矩阵（内存缓存，写入后自动失效重载）"""
    global _matrix_cache
    with _lock:
        if _matrix_cache is not None and _matrix_cache["version"] == version:
            return _matrix_cache

        db = SessionLocal()
        try:
            rows = db.scalars(select(QaCache).where(QaCache.content_version == version)).all()
            ids: list[int] = []
            vecs: list[np.ndarray] = []
            for r in rows:
                if r.question_vector:
                    ids.append(r.id)
                    vecs.append(np.frombuffer(r.question_vector, dtype=np.float32))
            matrix = np.vstack(vecs) if vecs else None
            _matrix_cache = {"ids": ids, "matrix": matrix, "version": version}
            logger.info("缓存向量矩阵已加载：%s 条", len(ids))
            return _matrix_cache
        finally:
            db.close()
