# -*- coding: utf-8 -*-
"""
检索服务 —— 企业级"混合检索 + 精排"

四步走（每一步解决一类问题）：
  1. 向量检索 top 20：按"意思"找（能匹配"能听多久"↔"续航时间"）
  2. BM25 关键词检索 top 20：按"词"找（擅长精确命中"W1""8000Pa"这类词）
  3. RRF 融合：把两路结果按"名次成绩"合并去重（两路都靠前的片段排名最优）
  4. 精排模型 20→5：逐一仔细打分，挑出真正最相关的

最后再做相关性判断：精排分数全部低于阈值 → 判为"知识库中没找到"（兜底）。
"""
import logging

from ..config import settings
from ..database import SessionLocal
from .bm25_index import search as bm25_search
from .embeddings import get_embeddings
from .ingestion_service import get_content_version
from .reranker import rerank
from .vectorstore import search_by_vector

logger = logging.getLogger(__name__)

_RRF_K = 60  # RRF 融合算法的标准参数（越大，名次之间的分差越小）


def retrieve(
    question: str,
    top_k: int | None = None,
    query_vector: list[float] | None = None,
) -> tuple[list[dict], bool]:
    """
    检索与问题最相关的资料片段。

    query_vector: 可选——调用方已经算过问题向量时直接传入（省一次计算）。

    返回 (hits, is_fallback)：
      hits: [{index, chunk_id, document_id, filename, content, rerank_score}]
      is_fallback: True 表示知识库里没有相关内容（需要兜底回答）
    """
    top_k = top_k or settings.rerank_top_n

    # 内容版本号（BM25 索引缓存用）
    db = SessionLocal()
    try:
        version = get_content_version(db)
    finally:
        db.close()

    # ---- 1. 向量检索 ----
    vector = query_vector or get_embeddings().embed_query(question)
    vec_hits = search_by_vector(vector, k=settings.vector_top_k)

    # ---- 2. BM25 关键词检索 ----
    kw_hits = bm25_search(question, top_k=settings.bm25_top_k, version=version)

    # ---- 3. RRF 融合 ----
    fused = _rrf_fuse(vec_hits, kw_hits)
    if not fused:
        logger.info("检索结果为空（问题：%s）", question[:40])
        return [], True

    # ---- 4. 精排（候选太多会增加耗时，截到 30 条）----
    candidate_limit = settings.vector_top_k + settings.bm25_top_k
    ranked = rerank(question, fused[:candidate_limit], top_n=max(top_k * 2, 10))

    # ---- 5. 相关性阈值判断 ----
    good = [r for r in ranked if r["rerank_score"] >= settings.rerank_threshold][:top_k]

    hits: list[dict] = []
    for index, item in enumerate(good, start=1):
        hits.append(
            {
                "index": index,
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "filename": _extract_filename(item["text"]),
                "content": _strip_header(item["text"]),
                "rerank_score": item["rerank_score"],
            }
        )

    is_fallback = len(hits) == 0
    logger.info(
        "混合检索：向量 %s 条 + 关键词 %s 条 → 融合 %s 条 → 精排采用 %s 条%s（问题：%s）",
        len(vec_hits),
        len(kw_hits),
        len(fused),
        len(hits),
        "【兜底】" if is_fallback else "",
        question[:40],
    )
    return hits, is_fallback


def _rrf_fuse(vec_hits: list[dict], kw_hits: list[dict]) -> list[dict]:
    """
    RRF 融合算法（Reciprocal Rank Fusion）：
    每个片段得分 = 1/(60+向量名次) + 1/(60+关键词名次)。
    两路都排前面的片段得分最高——这就是"混合"的价值。
    """
    merged: dict[int, dict] = {}  # chunk_id -> {"item": ..., "score": ...}

    for rank, item in enumerate(vec_hits):
        entry = merged.setdefault(item["chunk_id"], {"item": item, "score": 0.0})
        entry["score"] += 1.0 / (_RRF_K + rank + 1)

    for rank, item in enumerate(kw_hits):
        entry = merged.setdefault(item["chunk_id"], {"item": item, "score": 0.0})
        entry["score"] += 1.0 / (_RRF_K + rank + 1)

    ordered = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    result: list[dict] = []
    for entry in ordered:
        item = dict(entry["item"])
        item["rrf_score"] = entry["score"]
        result.append(item)
    return result


def _extract_filename(text: str) -> str:
    """从片段内容头部解析来源文件名（头部格式：【文档：xxx】）"""
    if text.startswith("【文档："):
        return text.split("】", 1)[0].replace("【文档：", "")
    return "未知来源"


def _strip_header(text: str) -> str:
    """去掉片段头部的来源标记，只留正文（发给模型和展示用）"""
    if text.startswith("【文档：") and "】" in text:
        return text.split("】", 1)[1].lstrip("\n")
    return text
