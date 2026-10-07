# -*- coding: utf-8 -*-
r"""
DeepSeek 大模型客户端封装

三个要点：
  1. 没配置 API Key 时，给用户清晰的中文指引（而不是一堆英文报错）
  2. 统一超时/重试参数（网络波动自动重试 2 次）
  3. 测试模式：环境变量 RAG_FAKE_LLM=1 时用"假模型"（不联网、不花钱，
     用于自动化测试问答链路）
"""
import asyncio
import logging
import os

from langchain_core.messages import AIMessageChunk

from ..config import settings
from ..core.exceptions import AppException

logger = logging.getLogger(__name__)


class FakeStreamingModel:
    """
    测试用假模型：把一段固定回答逐字吐出（模拟流式生成）。
    仅在 RAG_FAKE_LLM=1 时启用，生产环境永远不会用到。
    """

    _ANSWER = (
        "您好！根据资料：W1 耳机的续航时间为 30 小时（关闭降噪），"
        "充电 10 分钟即可听歌 2 小时 [1]。如果您需要了解其他参数，欢迎继续提问～"
    )
    _REWRITE_ANSWER = "W1 耳机的防水等级是什么？"  # 供指代改写链路测试用

    async def astream(self, _messages):  # noqa: ANN001 —— 与真实模型保持同样的接口
        for ch in self._ANSWER:
            yield AIMessageChunk(content=ch)
            await asyncio.sleep(0.01)

    async def ainvoke(self, _messages):  # noqa: ANN001
        """非流式调用（指代改写等场景）"""
        return AIMessageChunk(content=self._REWRITE_ANSWER)


def get_chat_model(
    temperature: float | None = None,
    max_tokens: int | None = None,
):
    """
    获取 DeepSeek 对话模型实例。
    流式输出直接用 `.astream()`（无需额外开关）。
    """
    if os.environ.get("RAG_FAKE_LLM") == "1":
        logger.warning("当前使用测试用假模型（RAG_FAKE_LLM=1）")
        return FakeStreamingModel()

    if not settings.deepseek_api_key:
        raise AppException(
            "还没有配置 DeepSeek 的 API Key（门禁卡）。"
            "请打开 backend\\.env 文件，把 sk- 开头的 Key 填到 DEEPSEEK_API_KEY= 后面，"
            "保存后重启系统即可。",
            503,
        )

    from langchain_deepseek import ChatDeepSeek

    return ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        temperature=settings.deepseek_temperature if temperature is None else temperature,
        max_tokens=settings.deepseek_max_tokens if max_tokens is None else max_tokens,
        timeout=settings.deepseek_timeout_s,
        max_retries=2,  # 网络波动自动重试
    )
