# -*- coding: utf-8 -*-
"""管理后台相关接口的出入参定义"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KbCreate(BaseModel):
    name: str = Field(..., max_length=50)
    description: str = Field("", max_length=500)

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("知识库名称不能为空")
        if len(v) > 50:
            raise ValueError("知识库名称最多 50 个字")
        return v


class KbUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=500)


class KbOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0   # 包含几份文档
    chunk_count: int = 0      # 共切成几段

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_type: str
    size_bytes: int
    status: str                    # pending / processing / ready / failed
    error_msg: str | None = None
    chunk_count: int = 0
    processed_chunks: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
