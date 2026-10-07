# -*- coding: utf-8 -*-
r"""
向量模型封装 —— 把文字变成「数字 DNA」的本地 AI 模型（BGE）

负责三件事：
  1. 加载 bge-large-zh-v1.5 模型（优先用显卡，不够自动回落 CPU）
  2. 查询侧自动加官方要求的前缀（不加会让检索准确率下降 10%~15%）
  3. 服务启动时后台"预热"，消灭"第一次提问特别慢"的问题

模型文件位置：F:\LangchainRAG-data\models\bge-large-zh-v1.5（由 2-下载模型.bat 下载）
"""
import logging
import threading

from langchain_huggingface import HuggingFaceEmbeddings

from ..config import settings

logger = logging.getLogger(__name__)

# BGE 中文 v1.5 系列官方要求的查询前缀（文档侧不加，查询侧必须加）
_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

_embeddings: "BgeChineseEmbeddings | None" = None
_emb_lock = threading.Lock()

# 模型状态（供健康检查/管理界面显示）
model_status: dict = {"state": "unloaded", "device": None, "error": None}


class BgeChineseEmbeddings(HuggingFaceEmbeddings):
    """BGE 中文模型封装：查询侧自动补前缀，文档侧保持原样"""

    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(_QUERY_PREFIX + text)


def _resolve_device() -> str:
    """
    决定用显卡还是 CPU：
      - .env 里写了 cuda/cpu → 就按写的来
      - auto（默认）→ 有显卡且空闲显存 ≥ 2GB 就用显卡，否则 CPU
    """
    pref = (settings.model_device or "auto").lower()
    if pref in ("cuda", "cpu"):
        return pref
    try:
        import torch

        if torch.cuda.is_available():
            free_bytes, _total = torch.cuda.mem_get_info()
            if free_bytes / 1024**3 >= 2.0:
                return "cuda"
            logger.warning("显卡空闲显存不足 2GB，向量模型改用 CPU 运行")
    except Exception:  # noqa: BLE001 —— 探测失败就保守用 CPU
        pass
    return "cpu"


def get_embeddings() -> BgeChineseEmbeddings:
    """获取向量模型单例（第一次调用时真正加载，之后直接复用）"""
    global _embeddings
    if _embeddings is None:
        with _emb_lock:
            if _embeddings is None:
                device = _resolve_device()
                try:
                    _embeddings = _build(device)
                except Exception as exc:  # noqa: BLE001
                    if device == "cuda":
                        logger.warning("显卡加载向量模型失败（%s），自动回落 CPU", exc)
                        _embeddings = _build("cpu")
                    else:
                        raise
                model_status.update(state="ready", device=_embeddings.model_kwargs.get("device"))
                logger.info("向量模型加载完成（设备：%s）", model_status["device"])
    return _embeddings


def _build(device: str) -> BgeChineseEmbeddings:
    return BgeChineseEmbeddings(
        model_name=settings.embedding_model_path,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 64},
    )


def warm_up_async() -> None:
    """服务启动时调用：后台线程预热模型，不阻塞启动"""

    def _warm():
        try:
            model_status.update(state="loading")
            emb = get_embeddings()
            emb.embed_query("预热")  # 跑一次真实编码，把显卡/内存都"热"起来
            logger.info("向量模型预热完成")
        except Exception as exc:  # noqa: BLE001
            model_status.update(state="failed", error=str(exc))
            logger.exception("向量模型预热失败")

    threading.Thread(target=_warm, daemon=True, name="embedding-warmup").start()
