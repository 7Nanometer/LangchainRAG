# -*- coding: utf-8 -*-
"""知识库表：一个知识库 = 一类资料的集合（本项目默认只有一个「电商商品知识库」）"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    # 内容版本号：知识库内容每变一次就 +1。
    # 作用：让"旧问答缓存"和"旧关键词索引"自动失效，保证答案用的永远是最新资料
    index_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
