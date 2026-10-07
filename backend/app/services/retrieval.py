# -*- coding: utf-8 -*-
"""
检索服务 —— 从知识库找到与问题最相关的资料片段

M3 版本：向量检索 + 相关性阈值兜底
（M4 里程碑将升级为：BM25 关键词 + 向量双路召回 → 精排模型 + 更精准的阈值）
"""
import logging

from ..config import settings
from .embeddings import get_embeddings
from .vectorstore import search_by_vector

logger = logging.getLogger(__name__)

# 相关性兜底阈值（余弦距离：越小越相关）。
# 依据实测数据：正确命中的距离约 0.85~1.3，明显无关的在 1.5 以上。
# 如果最相似片段的距离都超过它，就判断为"知识库里没有相关内容"。
MAX_DISTANCE = 1.5


def retrieve(question: str, top_k: int | None = None) -> tuple[list[dict], bool]:
    """
    检索与问题最相关的资料片段。

    返回 (hits, is_fallback)：
      hits: [{index, chunk_id, document_id, filename, content, distance}]
      is_fallback: True 表示什么都没找到（需要兜底回答"资料里没有"）
    """
    top_k = top_k or settings.rerank_top_n

    # 1. 问题 → 数字 DNA（查询侧自动带官方前缀，见 embeddings.py）
    vector = get_embeddings().embed_query(question)

    # 2. 向量检索取候选（多取一些，再过滤）
    candidates = search_by_vector(vector, k=max(top_k * 2, 8))

    # 3. 阈值过滤 + 取前 top_k
    good = [c for c in candidates if c["distance"] <= MAX_DISTANCE][:top_k]

    hits: list[dict] = []
    for index, item in enumerate(good, start=1):
        hits.append(
            {
                "index": index,
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "filename": _extract_filename(item["text"]),
                "content": _strip_header(item["text"]),
                "distance": item["distance"],
            }
        )

    is_fallback = len(hits) == 0
    logger.info(
        "检索完成：候选 %s 条 → 采用 %s 条%s（问题：%s）",
        len(candidates),
        len(hits),
        "【兜底】" if is_fallback else "",
        question[:40],
    )
    return hits, is_fallback


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
