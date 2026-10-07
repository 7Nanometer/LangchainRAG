# -*- coding: utf-8 -*-
"""
问答编排 —— 一次提问背后的完整流程（本项目的核心）

M4 升级版流程：
  1. 找到/创建会话，把用户的问题存进数据库
  2. 多轮场景先做「指代改写」（"它防水吗" → "W1 耳机防水吗"）
  3. 查「语义缓存」——问过/相似的问题直接秒回
  4. 检索资料（混合检索：向量 + 关键词 → 融合 → 精排；见 retrieval.py）
  5. 组装中文提示词，流式调用 DeepSeek，逐字推送（SSE 事件流）
  6. 完整答案 + 引用快照落库；写缓存供下次秒回
     （中途被停止也会保存已生成的部分）

SSE 事件协议（前端按事件名处理）：
  meta      最先发：会话 id、消息 id、是否兜底、是否缓存命中
  citations 生成前发：引用的资料片段列表
  delta     逐字发：本段新增文字
  done      结束：消息 id、耗时、是否来自缓存
  error     出错：中文错误信息
"""
import asyncio
import json
import logging
import time

from sqlalchemy import select

from ..core.exceptions import AppException
from ..database import SessionLocal
from ..models import Document, Message
from ..prompts.qa import build_qa_messages
from ..prompts.rewrite import build_rewrite_messages
from ..utils.sse import sse_comment, sse_event
from .cache_service import find_cached, save_cache
from .conversation_service import get_or_create_for_chat
from .embeddings import get_embeddings
from .ingestion_service import get_content_version
from .llm import get_chat_model
from .retrieval import retrieve

logger = logging.getLogger(__name__)

_HISTORY_ROUNDS = 3          # 携带最近几轮对话
_REWRITE_MAX_LEN = 12        # 短于这个长度的问题在多轮时尝试改写
_PRONOUNS = ("它", "他", "她", "这个", "那个", "这款", "那款", "该", "此", "上面", "刚才", "这", "那")


async def stream_chat(user_id: int, question: str, conversation_id: int | None):
    """问答流生成器：产出已格式化好的 SSE 事件字符串"""
    db = SessionLocal()
    started = time.perf_counter()
    answer_parts: list[str] = []
    citations: list[dict] = []
    assistant_msg: Message | None = None
    finished = False
    cache_saved = False

    try:
        yield sse_comment("processing")

        # ---- 1. 会话与用户消息 ----
        conv = get_or_create_for_chat(db, user_id, conversation_id, question)
        user_msg = Message(conversation_id=conv.id, role="user", content=question)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        history = _recent_history(db, conv.id, exclude_id=user_msg.id)

        # ---- 2. 指代改写（仅多轮且问题疑似不完整时）----
        search_question = question
        if history and _need_rewrite(question):
            rewritten = await _rewrite_question(question, history)
            if rewritten:
                search_question = rewritten
                user_msg.rewritten_question = rewritten
                db.commit()
                logger.info("指代改写：%s → %s", question[:30], rewritten[:40])

        # ---- 3. 问题向量（缓存查询 + 检索共用，只算一次）----
        question_vector = await asyncio.to_thread(
            get_embeddings().embed_query, search_question
        )
        version = await asyncio.to_thread(_content_version)

        # ---- 4. 语义缓存 ----
        cached = await asyncio.to_thread(find_cached, search_question, question_vector, version)
        if cached:
            latency_ms = int((time.perf_counter() - started) * 1000)
            assistant_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=cached["answer"],
                citations_json=json.dumps(cached["citations"], ensure_ascii=False),
                from_cache=1,
                latency_ms=latency_ms,
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            finished = True

            yield sse_event(
                "meta",
                {
                    "conversation_id": conv.id,
                    "user_message_id": user_msg.id,
                    "assistant_message_id": assistant_msg.id,
                    "is_fallback": False,
                    "from_cache": True,
                },
            )
            yield sse_event("citations", cached["citations"])
            # 缓存命中：整段一次性推送（"秒回"体验）
            yield sse_event("delta", {"text": cached["answer"]})
            yield sse_event(
                "done",
                {"message_id": assistant_msg.id, "latency_ms": latency_ms, "from_cache": True},
            )
            return

        # ---- 5. 混合检索（向量 + 关键词 → 融合 → 精排）----
        hits, is_fallback = await asyncio.to_thread(retrieve, question=search_question, top_k=None, query_vector=question_vector)

        # 兜底时：告诉模型"知识库收录了什么"，让回答更有帮助
        fallback_extra = None
        if is_fallback:
            fallback_extra = await asyncio.to_thread(_kb_document_names)

        # ---- 6. 助手消息占位 ----
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
                "score": round(h["rerank_score"], 4),  # 精排相关度（0~1）
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
                "from_cache": False,
            },
        )
        yield sse_event("citations", citations)

        # ---- 7. 流式生成 ----
        model = get_chat_model()
        messages = build_qa_messages(question, hits, history, fallback_extra=fallback_extra)
        async for chunk in model.astream(messages):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if not text:
                continue
            answer_parts.append(text)
            yield sse_event("delta", {"text": text})

        # ---- 8. 完成落库 ----
        answer_text = "".join(answer_parts)
        latency_ms = int((time.perf_counter() - started) * 1000)
        assistant_msg.content = answer_text
        assistant_msg.citations_json = json.dumps(citations, ensure_ascii=False)
        assistant_msg.is_fallback = 1 if is_fallback else 0
        assistant_msg.latency_ms = latency_ms
        db.commit()

        # ---- 9. 写语义缓存（兜底回答不缓存）----
        if not is_fallback and answer_text:
            await asyncio.to_thread(
                save_cache,
                search_question,
                question_vector,
                answer_text,
                assistant_msg.citations_json,
                version,
            )
            cache_saved = True

        finished = True
        logger.info(
            "问答完成：%s 字 / %s ms / 引用 %s 段（问题：%s）",
            len(answer_text),
            latency_ms,
            len(citations),
            question[:40],
        )
        yield sse_event(
            "done",
            {"message_id": assistant_msg.id, "latency_ms": latency_ms, "from_cache": False},
        )

    except AppException as exc:
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
        _ = cache_saved  # 供调试用（当前无需额外处理）


def _need_rewrite(question: str) -> bool:
    """判断是否需要指代改写：短问题或含代词的问题（多轮时）"""
    if len(question) <= _REWRITE_MAX_LEN:
        return True
    return any(p in question for p in _PRONOUNS)


async def _rewrite_question(question: str, history: list[tuple[str, str]]) -> str | None:
    """用大模型把问题改写成可独立检索的完整问句；失败返回 None（用原问题）"""
    try:
        model = get_chat_model(temperature=0.0, max_tokens=100)
        messages = build_rewrite_messages(question, history)
        response = await model.ainvoke(messages)
        text = str(response.content or "").strip().strip("“”\"'").strip()
        if 0 < len(text) <= 100 and text != question:
            return text
    except Exception:  # noqa: BLE001
        logger.exception("指代改写失败，改用原问题检索")
    return None


def _content_version() -> int:
    db = SessionLocal()
    try:
        return get_content_version(db)
    finally:
        db.close()


def _kb_document_names(limit: int = 8) -> str:
    """知识库里已收录的文档名（兜底回答时告诉用户"我们有哪些资料"）"""
    db = SessionLocal()
    try:
        names = list(
            db.scalars(
                select(Document.filename)
                .where(Document.status == "ready")
                .order_by(Document.created_at.desc())
                .limit(limit)
            )
        )
        return "、".join(names)
    finally:
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
