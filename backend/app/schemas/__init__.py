# -*- coding: utf-8 -*-
"""接口出入参定义汇总"""
from .admin import DocumentOut, KbCreate, KbOut, KbUpdate
from .auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserOut,
)
from .chat import ChatRequest
from .conversation import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    FeedbackRequest,
    MessageOut,
)

__all__ = [
    # 认证
    "RegisterRequest",
    "LoginRequest",
    "ChangePasswordRequest",
    "UserOut",
    # 管理
    "KbCreate",
    "KbUpdate",
    "KbOut",
    "DocumentOut",
    # 问答
    "ChatRequest",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationOut",
    "MessageOut",
    "FeedbackRequest",
]
