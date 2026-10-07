# -*- coding: utf-8 -*-
"""认证相关接口的出入参定义（自动校验格式，并给中文提示）"""
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=32)
    password: str = Field(..., max_length=64)

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"[\w一-龥]{3,20}", v):
            raise ValueError("用户名只能是 3~20 位的字母、数字、下划线或汉字")
        return v

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("密码必须同时包含字母和数字（例如 demo12345）")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., max_length=64)

    @field_validator("new_password")
    @classmethod
    def _check_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("新密码至少 8 位")
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("新密码必须同时包含字母和数字")
        return v


class UserOut(BaseModel):
    """返回给前端的用户信息（绝不包含密码相关字段）"""

    id: int
    username: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
