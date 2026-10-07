# -*- coding: utf-8 -*-
"""
问答编排 —— 一次提问背后的完整流程（本项目的核心）

流程：
  1. 找到/创建会话，把用户的问题存进数据库
  2. 检索资料（向量检索 + 相关性判断）
  3. 组装中文提示词（问题 + 参考资料 + 最近几轮对话）
  4. 流式调用 DeepSeek，逐字推送（SSE 事件流）
  5. 完整答案 + 引用快照落库（中途被停止也会保存已生成的部分）

SSE 事件协议（前端按事件名处理）：
  meta      最先发：会话 id、消息 id、是否兜底
  citations 生成前发：引用的资料片段列表
  delta     逐字发：本段新增文字
  done      结束：消息 id、耗时
  error     出错：中文错误信息
"""
import asyncio
import json
import logging
import time

from sqlalchemy import select

from ..core.exceptions import AppException
from ..database import SessionLocal
from ..models import Message
from ..prompts.qa import build_qa_messages
from ..utils.sse import sse_comment, sse_event
from .conversation_service import get_or_create_for_chat
from .llm import get_chat_model
from .retrieval import retrieve

logger = logging.getLogger(__name__)

_HISTORY_ROUNDS = 3  # 携带最近几轮对话，让模型理解"它""这个"之类的指代


async def stream_chat(user_id: int, question: str, conversation_id: int | None):
    """
    问答流生成器：产出已格式化好的 SSE 事件字符串。
    由 api/chat.py 包装成 StreamingResponse 发给浏览器。
    """
    db = SessionLocal()
    started = time.perf_counter()
    answer_parts: list[str] = []
    citations: list[dict] = []
    assistant_msg: Message | None = None
    finished = False  # 是否正常走完（用于判断"被中断"）

    try:
        # 先发一个心跳，告诉前端连接正常、正在准备
        yield sse_comment("processing")

        # ---- 1. 会话与用户消息 ----
        conv = get_or_create_for_chat(db, user_id, conversation_id, question)
        user_msg = Message(conversation_id=conv.id, role="user", content=question)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        history = _recent_history(db, conv.id, exclude_id=user_msg.id)

        # ---- 2. 检索资料（阻塞操作放线程池；首次运行还要加载模型，不能让界面卡住）----
        hits, is_fallback = await asyncio.to_thread(retrieve, question)

        # ---- 3. 助手消息占位（先落库，之后逐步补内容；中断也有记录）----
        assistant_msg = Message(
            conversation_id=conv.id, role="assistant", content="", citations_json="[]"
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        citations = [
            {
                "index": h["index"],
                "filename": h["filename"],
                "content": h["content"],
                "score": round(1 - h["distance"], 4),  # 相似度分数（越大越相关）
            }
            for h in hits
        ]

        yield sse_event(
            "meta",
            {
                "conversation_id": conv.id,
                "user_message_id": user_msg.id,
                "assistant_message_id": assistant_msg.id,
                "is_fallback": is_fallback,
            },
        )
        yield sse_event("citations", citations)

        # ---- 4. 流式生成 ----
        model = get_chat_model()
        messages = build_qa_messages(question, hits, history)
        async for chunk in model.astream(messages):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if not text:
                continue
            answer_parts.append(text)
            yield sse_event("delta", {"text": text})

        # ---- 5. 完成落库 ----
        latency_ms = int((time.perf_counter() - started) * 1000)
        assistant_msg.content = "".join(answer_parts)
        assistant_msg.citations_json = json.dumps(citations, ensure_ascii=False)
        assistant_msg.is_fallback = 1 if is_fallback else 0
        assistant_msg.latency_ms = latency_ms
        db.commit()
        finished = True
        logger.info(
            "问答完成：%s 字 / %s ms / 引用 %s 段（问题：%s）",
            len(assistant_msg.content),
            latency_ms,
            len(citations),
            question[:40],
        )
        yield sse_event("done", {"message_id": assistant_msg.id, "latency_ms": latency_ms})

    except AppException as exc:
        # 业务错误（如未配置 Key）→ 以中文错误事件发给前端
        yield sse_event("error", {"message": exc.message})
    except Exception:  # noqa: BLE001
        logger.exception("问答流处理失败")
        yield sse_event("error", {"message": "回答生成失败，请稍后重试（详情见系统日志）"})
    finally:
        # ---- 中断保护：用户点"停止"或断网时，保存已生成的部分 ----
        try:
            if assistant_msg is not None and not finished and answer_parts:
                db.refresh(assistant_msg)
                if not assistant_msg.content:
                    assistant_msg.content = "".join(answer_parts) + "……（回答已中断）"
                    assistant_msg.citations_json = json.dumps(citations, ensure_ascii=False)
                    assistant_msg.latency_ms = int((time.perf_counter() - started) * 1000)
                    db.commit()
                    logger.info("已保存被中断的回答（%s 字）", len(answer_parts))
        except Exception:  # noqa: BLE001
            logger.exception("保存被中断的回答失败")
        db.close()


def _recent_history(db, conversation_id: int, exclude_id: int, rounds: int = _HISTORY_ROUNDS):
    """取本会话最近几轮对话（不含刚存进去的这条提问）"""
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.id != exclude_id)
        .order_by(Message.id.desc())
        .limit(rounds * 2)
    ).all()
    return [(m.role, m.content) for m in reversed(messages) if m.content]
