# -*- coding: utf-8 -*-
"""会话表：一段对话 = 一个会话（类似微信里的一个聊天窗口）"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(100), default="新会话")
    # 软删除：删除会话时只把这里标成 1，数据仍保留在数据库里（防误删、可恢复）
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # 组合索引：让「显示我的会话列表（按最近使用排序）」这条查询飞快
    __table_args__ = (
        Index("ix_conversations_user_active", "user_id", "is_deleted", "updated_at"),
    )
