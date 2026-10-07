# -*- coding: utf-8 -*-
"""文档表：管理员上传的每一份资料文件"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))          # 原始文件名（显示用）
    file_path: Mapped[str] = mapped_column(String(500))         # 存在服务器上的路径
    file_type: Mapped[str] = mapped_column(String(16))          # pdf / docx / xlsx / csv / txt / md
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # 处理状态：pending=排队中 ｜ processing=处理中 ｜ ready=已完成 ｜ failed=失败
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    # 失败原因（中文，直接展示给管理员）
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunk_count: Mapped[int] = mapped_column(Integer, default=0)        # 总共切成了几段
    processed_chunks: Mapped[int] = mapped_column(Integer, default=0)   # 已处理几段（进度条用）

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
