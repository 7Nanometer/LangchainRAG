# -*- coding: utf-8 -*-
"""消息接口：点赞 / 点踩"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas.conversation import FeedbackRequest
from ..services import conversation_service

router = APIRouter(prefix="/messages", tags=["消息"])


@router.put("/{message_id}/feedback", summary="点赞/点踩/取消评价")
def update_feedback(
    message_id: int,
    payload: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = conversation_service.update_feedback(db, user.id, message_id, payload.feedback)
    return {"message": "感谢反馈", "feedback": msg.feedback}
