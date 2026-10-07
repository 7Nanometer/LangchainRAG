# -*- coding: utf-8 -*-
"""会话与消息相关接口的出入参定义"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ConversationCreate(BaseModel):
    title: str = Field("新会话", max_length=50)


class ConversationUpdate(BaseModel):
    title: str = Field(..., max_length=50)

    @field_validator("title")
    @classmethod
    def _check_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("会话标题不能为空")
        return v


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageOut(BaseModel):
    id: int
    role: str                       # user / assistant
    content: str
    citations: list = []            # 引用快照（历史回看时原样展示）
    feedback: str | None = None     # like / dislike / None
    is_fallback: bool = False       # 是否为兜底回答
    from_cache: bool = False        # 是否来自缓存（M4）
    latency_ms: int = 0
    created_at: datetime


class FeedbackRequest(BaseModel):
    feedback: str | None = None     # like / dislike / null（取消评价）

    @field_validator("feedback")
    @classmethod
    def _check_feedback(cls, v):
        if v not in (None, "like", "dislike"):
            raise ValueError("评价类型不正确")
        return v
