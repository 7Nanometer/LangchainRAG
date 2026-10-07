# -*- coding: utf-8 -*-
r"""
精排模型封装 —— 检索结果的专业"面试官"

粗召回（向量 + 关键词）会挑出几十个候选片段，其中混着一些不太相关的。
精排模型把「问题 + 片段」放在一起**逐个仔细打量**，打出精确的相关性分数，
挑出真正最好的那几个交给 AI 写答案。

模型：bge-reranker-v2-m3（约 2.2GB，可从显卡自动回落 CPU）
位置：F:\LangchainRAG-data\models\bge-reranker-v2-m3
"""
import logging
import threading

from ..config import settings

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()
model_status: dict = {"state": "unloaded", "device": None, "error": None}


def _resolve_device() -> str:
    """自动选择计算设备（显卡空闲显存 ≥ 1.5GB 才用显卡）"""
    pref = (settings.model_device or "auto").lower()
    if pref in ("cuda", "cpu"):
        return pref
    try:
        import torch

        if torch.cuda.is_available():
            free_bytes, _total = torch.cuda.mem_get_info()
            if free_bytes / 1024**3 >= 1.5:
                return "cuda"
            logger.warning("显卡空闲显存不足 1.5GB，精排模型改用 CPU")
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


def get_reranker():
    """获取精排模型单例（第一次调用时加载）"""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import CrossEncoder

                device = _resolve_device()
                try:
                    _model = _build(device)
                except Exception as exc:  # noqa: BLE001
                    if device == "cuda":
                        logger.warning("显卡加载精排模型失败（%s），回落 CPU", exc)
                        _model = _build("cpu")
                    else:
                        raise
                model_status.update(state="ready", device=device)
                logger.info("精排模型加载完成（设备：%s）", device)
    return _model


def _build(device: str):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        settings.reranker_model_path,
        device=device,
        max_length=512,  # 问题+片段的总长度上限
    )


def rerank(question: str, items: list[dict], top_n: int) -> list[dict]:
    """
    给候选片段精排打分。
    返回带 rerank_score（0~1，越大越相关）的列表，按分数从高到低取前 top_n。
    """
    if not items:
        return []

    model = get_reranker()
    pairs = [(question, it["text"]) for it in items]
    raw_scores = model.predict(pairs, batch_size=16)

    scored: list[dict] = []
    for item, raw in zip(items, raw_scores):
        item = dict(item)
        # 模型输出的是原始分数，用 sigmoid 换算成 0~1 的"相关度"
        import math

        item["rerank_score"] = 1.0 / (1.0 + math.exp(-float(raw)))
        scored.append(item)

    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored[:top_n]


def warm_up_async() -> None:
    """服务启动时后台预热（提前加载模型，第一问不用等）"""
    def _warm():
        try:
            model_status.update(state="loading")
            model = get_reranker()
            model.predict([("预热", "预热文本")], batch_size=1)  # 跑一次真实打分
            logger.info("精排模型预热完成")
        except Exception as exc:  # noqa: BLE001
            model_status.update(state="failed", error=str(exc))
            logger.exception("精排模型预热失败")

    threading.Thread(target=_warm, daemon=True, name="reranker-warmup").start()
