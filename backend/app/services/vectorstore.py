# -*- coding: utf-8 -*-
r"""
向量库封装 —— 存放所有资料片段的「数字 DNA」

两个关键设计：
  1. 单进程访问 + 写锁：Chroma 是"文件型"向量库，多个进程同时写会写坏，
     所以全项目只允许一个服务进程（启动脚本已固定单 worker），
     并且所有写操作排队进行（写锁）。
  2. 分批写入：一次写 200 条，大文件入库时不撑爆内存。

数据位置：E:\Vibe Coding\LangchainRAG项目\backend\data\chroma
"""
import logging
import threading

import chromadb
from langchain_chroma import Chroma

from ..config import CHROMA_DIR
from .embeddings import get_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kb_chunks"
_BATCH_SIZE = 200  # 每批写入条数

_client = None
_client_lock = threading.Lock()
_write_lock = threading.RLock()  # 写操作互斥锁


def get_client():
    """获取 Chroma 客户端单例（PersistentClient = 数据存本地磁盘）"""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
                logger.info("向量库已连接：%s", CHROMA_DIR)
    return _client


def get_vectorstore() -> Chroma:
    """LangChain 风格的向量库对象（用我们的 BGE 模型做向量化）"""
    return Chroma(
        client=get_client(),
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )


def add_texts(ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    """分批把片段写入向量库（自动向量化；带写锁防并发冲突）"""
    vs = get_vectorstore()
    with _write_lock:
        for i in range(0, len(ids), _BATCH_SIZE):
            batch_ids = ids[i : i + _BATCH_SIZE]
            batch_texts = texts[i : i + _BATCH_SIZE]
            batch_metas = metadatas[i : i + _BATCH_SIZE]
            vs.add_texts(texts=batch_texts, metadatas=batch_metas, ids=batch_ids)
            logger.info("向量库写入进度：%s / %s", min(i + _BATCH_SIZE, len(ids)), len(ids))


def delete_where(where: dict) -> None:
    """按条件删除向量（如删除某文档、某知识库的全部向量）"""
    with _write_lock:
        collection = get_client().get_or_create_collection(COLLECTION_NAME)
        collection.delete(where=where)
        logger.info("已删除向量：%s", where)


def search_by_vector(vector: list[float], k: int = 20, where: dict | None = None) -> list[dict]:
    """
    向量检索：给一串「数字 DNA」，找出最相似的 k 个片段。

    返回：[{chunk_id, document_id, kb_id, text, distance}, ...]（按相似度排序）
    M3/M4 的问答检索会使用它。
    """
    with _write_lock:  # 读也加锁：避免查询和写入交错导致瞬时不一致（本机场景开销可忽略）
        collection = get_client().get_or_create_collection(COLLECTION_NAME)
        result = collection.query(
            query_embeddings=[vector],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    items: list[dict] = []
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]
    for chunk_id, text, meta, dist in zip(ids, docs, metas, dists):
        meta = meta or {}
        items.append(
            {
                "chunk_id": meta.get("chunk_id") or chunk_id,
                "document_id": meta.get("document_id"),
                "kb_id": meta.get("kb_id"),
                "text": text,
                "distance": dist,
            }
        )
    return items


def total_count() -> int:
    """向量库里的片段总数（管理界面/看板显示用）"""
    try:
        return get_client().get_or_create_collection(COLLECTION_NAME).count()
    except Exception:  # noqa: BLE001
        return 0
