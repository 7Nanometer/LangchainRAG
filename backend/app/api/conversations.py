# -*- coding: utf-8 -*-
"""会话管理接口：列表 / 新建 / 改名 / 删除 / 消息读取 / 导出"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas.conversation import ConversationCreate, ConversationOut, ConversationUpdate
from ..services import conversation_service

router = APIRouter(prefix="/conversations", tags=["会话"])


@router.get("", summary="我的会话列表")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return conversation_service.list_conversations(db, user.id)


@router.post("", summary="新建会话")
def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = conversation_service.create_conversation(db, user.id, payload.title)
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.patch("/{conversation_id}", summary="重命名会话")
def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = conversation_service.rename_conversation(db, user.id, conversation_id, payload.title)
    return {"message": "已重命名", "title": conv.title}


@router.delete("/{conversation_id}", summary="删除会话（软删除）")
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation_service.delete_conversation(db, user.id, conversation_id)
    return {"message": "会话已删除"}


@router.get("/{conversation_id}/messages", summary="会话的全部消息")
def list_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return conversation_service.list_messages(db, user.id, conversation_id)


@router.get("/{conversation_id}/export", summary="导出会话为 Markdown")
def export_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename, content = conversation_service.export_markdown(db, user.id, conversation_id)
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={
            # filename*=UTF-8''... 让中文文件名正确下载（HTTP 标准写法）
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        },
    )
