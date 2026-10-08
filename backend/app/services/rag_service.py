# -*- coding: utf-8 -*-
"""
问答编排 —— 一次提问背后的完整流程（本项目的核心）

流程：
  1. 找到/创建会话，把用户的问题存进数据库
  2. 多轮场景先做「指代改写」（"它防水吗" → "W1 耳机防水吗"）
  3. 查「语义缓存」——问过/相似的问题直接秒回
  4. 检索资料（混合检索：向量 + 关键词 → 融合 → 精排；见 retrieval.py）
  5. 组装中文提示词，流式调用 DeepSeek，逐字推送（SSE 事件流）
  6. 完整答案 + 引用快照落库；写缓存供下次秒回

【并发设计（压测调优后）】
  - 所有数据库操作都封装成"独立短连接函数"，通过线程池执行（asyncio.to_thread），
    绝不占用事件循环——否则一次数据库等锁会卡住所有人的请求（压测实测复现过）
  - 写操作尽量合并（一次提交多条），减少 SQLite 写锁竞争
  - 中断保存用独立线程执行（不阻塞、不 await）

SSE 事件协议：meta → citations → delta（多次）→ done / error
"""
import asyncio
import json
import logging
import re
import threading
import time

from sqlalchemy import select

from ..config import settings
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
    started = time.perf_counter()
    answer_parts: list[str] = []
    citations: list[dict] = []
    assistant_id: int | None = None
    user_msg_id: int | None = None
    rewritten: str | None = None
    finished = False

    try:
        yield sse_comment("processing")

        # ---- 1. 会话 + 用户消息 + 历史（一次线程池往返，不阻塞事件循环）----
        conv_id, user_msg_id, history = await asyncio.to_thread(
            _db_prepare_chat, user_id, conversation_id, question
        )

        # ---- 2. 指代改写（仅多轮且问题疑似不完整时）----
        search_question = question
        if history and _need_rewrite(question):
            rewritten = await _rewrite_question(question, history)
            if rewritten:
                search_question = rewritten
                logger.info("指代改写：%s → %s", question[:30], rewritten[:40])

        # ---- 3. 问题向量（缓存查询 + 检索共用，只算一次）----
        question_vector = await asyncio.to_thread(
            get_embeddings().embed_query, search_question
        )
        version = await asyncio.to_thread(_content_version)

        # ---- 4. 语义缓存（可按配置关闭）----
        cached = None
        if settings.qa_cache_enabled:
            cached = await asyncio.to_thread(
                find_cached, search_question, question_vector, version
            )
        if cached:
            latency_ms = int((time.perf_counter() - started) * 1000)
            assistant_id = await asyncio.to_thread(
                _db_create_cached_answer,
                conv_id,
                cached["answer"],
                json.dumps(cached["citations"], ensure_ascii=False),
                latency_ms,
            )
            finished = True
            yield sse_event(
                "meta",
                {
                    "conversation_id": conv_id,
                    "user_message_id": user_msg_id,
                    "assistant_message_id": assistant_id,
                    "is_fallback": False,
                    "from_cache": True,
                },
            )
            yield sse_event("citations", cached["citations"])
            yield sse_event("delta", {"text": cached["answer"]})
            yield sse_event(
                "done",
                {"message_id": assistant_id, "latency_ms": latency_ms, "from_cache": True},
            )
            return

        # ---- 5. 混合检索（向量 + 关键词 → 融合 → 精排）----
        hits, is_fallback = await asyncio.to_thread(
            retrieve, question=search_question, top_k=None, query_vector=question_vector
        )

        fallback_extra = None
        if is_fallback:
            fallback_extra = await asyncio.to_thread(_kb_document_names)

        # ---- 6. 助手消息占位（先落库，中断也有记录）----
        assistant_id = await asyncio.to_thread(_db_create_placeholder, conv_id)

        citations = [
            {
                "index": h["index"],
                "filename": h["filename"],
                "content": h["content"],
                "score": round(h["rerank_score"], 4),
            }
            for h in hits
        ]

        yield sse_event(
            "meta",
            {
                "conversation_id": conv_id,
                "user_message_id": user_msg_id,
                "assistant_message_id": assistant_id,
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

        # ---- 8. 完成落库（一次提交：回答 + 改写记录）----
        answer_text = "".join(answer_parts)
        latency_ms = int((time.perf_counter() - started) * 1000)
        citations_json = json.dumps(citations, ensure_ascii=False)
        await asyncio.to_thread(
            _db_finish_answer,
            assistant_id,
            answer_text,
            citations_json,
            is_fallback,
            latency_ms,
            user_msg_id,
            rewritten,
        )

        # ---- 9. 写语义缓存（兜底回答不缓存；缓存可关闭）----
        if settings.qa_cache_enabled and not is_fallback and answer_text:
            await asyncio.to_thread(
                save_cache,
                search_question,
                question_vector,
                answer_text,
                citations_json,
                version,
            )

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
            {"message_id": assistant_id, "latency_ms": latency_ms, "from_cache": False},
        )

    except AppException as exc:
        yield sse_event("error", {"message": exc.message})
    except Exception:  # noqa: BLE001
        logger.exception("问答流处理失败")
        yield sse_event("error", {"message": "回答生成失败，请稍后重试（详情见系统日志）"})
    finally:
        # ---- 中断保护：用户点"停止"或断网时，保存已生成的部分 ----
        # （用独立线程执行——finally 里不能 await，也不能阻塞）
        if assistant_id is not None and not finished and answer_parts:
            threading.Thread(
                target=_db_save_partial,
                args=(
                    assistant_id,
                    "".join(answer_parts) + "……（回答已中断）",
                    json.dumps(citations, ensure_ascii=False),
                    int((time.perf_counter() - started) * 1000),
                ),
                daemon=True,
                name="partial-save",
            ).start()


# ---------------------------------------------------------------------------
# 数据库操作（每个函数独立短连接，供线程池调用——绝不跨线程共享 Session）
# ---------------------------------------------------------------------------


def _db_prepare_chat(
    user_id: int, conversation_id: int | None, question: str
) -> tuple[int, int, list[tuple[str, str]]]:
    """会话 + 用户消息一次搞定，并带回最近对话历史"""
    db = SessionLocal()
    try:
        conv = get_or_create_for_chat(db, user_id, conversation_id, question)
        user_msg = Message(conversation_id=conv.id, role="user", content=question)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)
        history = _recent_history(db, conv.id, exclude_id=user_msg.id)
        return conv.id, user_msg.id, history
    finally:
        db.close()


def _db_create_placeholder(conv_id: int) -> int:
    """创建"生成中"的助手消息占位，返回消息 id"""
    db = SessionLocal()
    try:
        msg = Message(conversation_id=conv_id, role="assistant", content="", citations_json="[]")
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg.id
    finally:
        db.close()


def _db_create_cached_answer(
    conv_id: int, answer: str, citations_json: str, latency_ms: int
) -> int:
    """缓存命中：一次性创建完整的助手消息"""
    db = SessionLocal()
    try:
        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content=answer,
            citations_json=citations_json,
            from_cache=1,
            latency_ms=latency_ms,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg.id
    finally:
        db.close()


def _db_finish_answer(
    assistant_id: int,
    content: str,
    citations_json: str,
    is_fallback: bool,
    latency_ms: int,
    user_msg_id: int | None,
    rewritten: str | None,
) -> None:
    """生成完成：写入完整回答 + 改写记录（一次提交）"""
    db = SessionLocal()
    try:
        msg = db.get(Message, assistant_id)
        if msg is not None:
            msg.content = content
            msg.citations_json = citations_json
            msg.is_fallback = 1 if is_fallback else 0
            msg.latency_ms = latency_ms
        if user_msg_id and rewritten:
            user_msg = db.get(Message, user_msg_id)
            if user_msg is not None:
                user_msg.rewritten_question = rewritten
        db.commit()
    finally:
        db.close()


def _db_save_partial(
    assistant_id: int, content: str, citations_json: str, latency_ms: int
) -> None:
    """保存被中断的部分回答（在独立线程中执行）"""
    db = SessionLocal()
    try:
        msg = db.get(Message, assistant_id)
        if msg is not None and not msg.content:
            msg.content = content
            msg.citations_json = citations_json
            msg.latency_ms = latency_ms
            db.commit()
            logger.info("已保存被中断的回答（%s 字）", len(content))
    except Exception:  # noqa: BLE001
        logger.exception("保存被中断的回答失败")
    finally:
        db.close()


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


def _need_rewrite(question: str) -> bool:
    """判断是否需要指代改写：短问题或含代词的问题（多轮时）"""
    if len(question) <= _REWRITE_MAX_LEN:
        return True
    return any(p in question for p in _PRONOUNS)


async def _rewrite_question(question: str, history: list[tuple[str, str]]) -> str | None:
    """
    用大模型把问题改写成可独立检索的完整问句；失败或无需改写时返回 None（用原问题）。

    注意：deepseek-flash 是"先思考再回答"的模型，max_tokens 必须给足，
    否则思考过程会把额度耗尽、正文为空（曾实测踩坑）。
    """
    try:
        model = get_chat_model(temperature=0.0, max_tokens=800)
        messages = build_rewrite_messages(question, history)
        response = await model.ainvoke(messages)

        text = str(response.content or "").strip()
        for quote in ('"', "'", "“", "”", "「", "」"):
            text = text.strip(quote)
        text = re.sub(r"^(改写后(的)?(检索)?(问题|问句)[：:]\s*)", "", text)
        text = text.split("\n")[0].strip()

        if not text:
            logger.warning("指代改写返回为空（可能 max_tokens 不足），改用原问题检索")
            return None
        if text == question:
            logger.info("指代改写：模型判定无需改写，按原问题检索")
            return None
        if len(text) > 100:
            logger.warning("指代改写结果过长，改用原问题检索：%s", text[:60])
            return None
        return text
    except Exception:  # noqa: BLE001
        logger.exception("指代改写失败，改用原问题检索")
    return None
