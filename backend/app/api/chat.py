# -*- coding: utf-8 -*-
"""
问答接口 —— 流式问答（SSE）

请求 POST /api/chat/stream  {question, conversation_id?}
返回事件流：meta → citations → delta（多次）→ done（或 error）

注意：本端点是 async 的（要返回流式响应），因此内部的数据库操作
必须放进线程池执行（asyncio.to_thread）——否则会阻塞事件循环，
高并发下拖垮整个服务（压测实测教训）。
"""
import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..core.exceptions import AppException
from ..core.limiter import check_rate_limit
from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import User
from ..schemas.chat import ChatRequest
from ..services.conversation_service import get_owned_conversation
from ..services.llm import get_chat_model
from ..services.rag_service import stream_chat

router = APIRouter(prefix="/chat", tags=["问答"])


def _verify_conversation_owner(user_id: int, conversation_id: int) -> None:
    """会话归属校验（独立短连接，供线程池调用）"""
    db = SessionLocal()
    try:
        get_owned_conversation(db, user_id, conversation_id)
    finally:
        db.close()


@router.post("/stream", summary="流式问答（打字机效果）")
async def chat_stream(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    在流开始之前做完所有"能提前做"的校验——
    这样这类错误能以正常的 HTTP 状态码返回（前端好处理），
    只有生成过程中的错误才通过 SSE 的 error 事件传递。
    """
    question = payload.question.strip()
    if not question:
        raise AppException("请输入要问的问题")
    if len(question) > 2000:
        raise AppException("问题太长了，请输入 2000 字以内的内容")

    # 每用户每分钟提问次数限制（防 API 费用失控）
    check_rate_limit(user.id)

    # 会话归属校验（防越权；放线程池执行，避免阻塞事件循环）
    if payload.conversation_id is not None:
        await asyncio.to_thread(_verify_conversation_owner, user.id, payload.conversation_id)

    # 提前检查模型配置（没配 API Key 时在这里就报中文错误，而不是流中断）
    get_chat_model()

    return StreamingResponse(
        stream_chat(user.id, question, payload.conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 防止中间层缓冲导致"攒完才显示"
        },
    )
