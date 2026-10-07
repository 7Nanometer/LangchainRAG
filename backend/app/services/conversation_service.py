# -*- coding: utf-8 -*-
"""会话与消息的业务逻辑：列表、新建、改名、删除、消息读取、导出"""
import json
import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import AppException
from ..models import Conversation, Message

logger = logging.getLogger(__name__)


def get_owned_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation:
    """取会话并校验归属（防止用户 A 通过 id 猜别人的会话）"""
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.is_deleted or conv.user_id != user_id:
        raise AppException("会话不存在", 404)
    return conv


def list_conversations(db: Session, user_id: int) -> list[dict]:
    """我的会话列表（最近使用的排前面，带消息条数）"""
    convs = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_deleted == 0)
        .order_by(Conversation.updated_at.desc())
        .limit(200)
    ).all()

    result = []
    for conv in convs:
        count = db.scalar(
            select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
        )
        result.append(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": count or 0,
            }
        )
    return result


def create_conversation(db: Session, user_id: int, title: str = "新会话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title.strip() or "新会话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def rename_conversation(db: Session, user_id: int, conversation_id: int, title: str) -> Conversation:
    conv = get_owned_conversation(db, user_id, conversation_id)
    conv.title = title.strip()[:50] or "新会话"
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, user_id: int, conversation_id: int) -> None:
    """软删除：标记删除，数据保留在库里（防误删）"""
    conv = get_owned_conversation(db, user_id, conversation_id)
    conv.is_deleted = 1
    db.commit()


def get_or_create_for_chat(
    db: Session, user_id: int, conversation_id: int | None, question: str
) -> Conversation:
    """
    问答用：有会话就用它；没有就新建一个（并自动用问题前 20 字命名）。
    """
    if conversation_id:
        conv = get_owned_conversation(db, user_id, conversation_id)
        if conv.title == "新会话":
            conv.title = _make_title(question)
        return conv

    conv = create_conversation(db, user_id, title=_make_title(question))
    return conv


def _make_title(question: str) -> str:
    """用问题的前 20 个字作为会话标题"""
    q = " ".join(question.strip().split())
    return q[:20] + ("…" if len(q) > 20 else "")


def list_messages(db: Session, user_id: int, conversation_id: int) -> list[dict]:
    conv = get_owned_conversation(db, user_id, conversation_id)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.id)
    ).all()
    return [message_to_dict(m) for m in messages]


def message_to_dict(m: Message) -> dict:
    """消息对象 → 前端 JSON（把 citations_json 解析成数组）"""
    try:
        citations = json.loads(m.citations_json or "[]")
    except (ValueError, TypeError):
        citations = []
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "citations": citations,
        "feedback": m.feedback,
        "is_fallback": bool(m.is_fallback),
        "from_cache": bool(m.from_cache),
        "latency_ms": m.latency_ms,
        "created_at": m.created_at,
    }


def export_markdown(db: Session, user_id: int, conversation_id: int) -> tuple[str, str]:
    """导出会话为 Markdown 文件，返回 (文件名, 内容)"""
    conv = get_owned_conversation(db, user_id, conversation_id)
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.id)
    ).all()

    lines: list[str] = [
        f"# {conv.title}",
        "",
        f"> 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　｜　知识库智能问答系统",
        "",
    ]
    for m in messages:
        if m.role == "user":
            lines += ["## 🙋 我", "", m.content, ""]
        else:
            lines += ["## 🤖 智能客服", "", m.content, ""]
            try:
                citations = json.loads(m.citations_json or "[]")
            except (ValueError, TypeError):
                citations = []
            if citations:
                lines.append("**引用来源：**")
                for c in citations:
                    lines.append(f"> [{c.get('index')}] {c.get('filename')}")
                lines.append("")
            if m.is_fallback:
                lines.append(">（本次回答为兜底回答：知识库中未找到相关资料）")
                lines.append("")

    filename = f"{conv.title}.md"
    return filename, "\n".join(lines)


def update_feedback(db: Session, user_id: int, message_id: int, feedback: str | None) -> Message:
    """点赞/点踩/取消（校验消息属于该用户的会话）"""
    msg = db.get(Message, message_id)
    if msg is None:
        raise AppException("消息不存在", 404)
    if msg.role != "assistant":
        raise AppException("只能对助手的回答进行评价")
    conv = db.get(Conversation, msg.conversation_id)
    if conv is None or conv.user_id != user_id:
        raise AppException("消息不存在", 404)
    msg.feedback = feedback
    db.commit()
    db.refresh(msg)
    return msg
