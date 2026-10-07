# -*- coding: utf-8 -*-
"""问答接口的出入参定义"""
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(..., max_length=2000)
    conversation_id: int | None = None   # 为空则自动新建会话

    @field_validator("question")
    @classmethod
    def _check_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("请输入要问的问题")
        return v
