# -*- coding: utf-8 -*-
"""接口出入参定义汇总"""
from .admin import DocumentOut, KbCreate, KbOut, KbUpdate
from .auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserOut,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "ChangePasswordRequest",
    "UserOut",
    "KbCreate",
    "KbUpdate",
    "KbOut",
    "DocumentOut",
]
