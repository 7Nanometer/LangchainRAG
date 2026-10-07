# -*- coding: utf-8 -*-
"""问答缓存表：把问过的答案存下来，相似的提问直接秒回（省钱、快）"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class QaCache(Base):
    __tablename__ = "qa_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(32), default="all")   # 预留：目前全部知识库共用
    question: Mapped[str] = mapped_column(Text)                     # 原问题文字
    # 问题"指纹"：把问题标准化（去空格/标点）后算的哈希值 —— 完全相同的问题秒查
    question_hash: Mapped[str] = mapped_column(String(64), index=True)
    # 问题的「数字 DNA」（1024 维 float32，共 4096 字节二进制）—— 相似度比对用
    question_vector: Mapped[bytes] = mapped_column(LargeBinary)

    answer: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[str] = mapped_column(Text, default="[]")

    hit_count: Mapped[int] = mapped_column(Integer, default=0)      # 被复用了几次
    # 缓存对应的知识库内容版本：知识库内容一更新，版本对不上，旧缓存自动作废
    content_version: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_hit_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("scope", "question_hash", name="uq_cache_q"),)
