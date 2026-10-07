# -*- coding: utf-8 -*-
"""文本片段表：文档被切成的每一小段（检索的最小单位）

设计说明：文字"正本"存在这里的 SQLite；Chroma 向量库里只存每段的
「数字 DNA」并带着 chunk_id 指回本表 —— 两个库职责分明，不会互相打架。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    # 冗余存一份知识库 ID：按知识库批量检索/删除时不用再联表，更快
    kb_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)   # 本片段是文档里的第几段
    content: Mapped[str] = mapped_column(Text)          # 片段文字（含「来源：文件名」头部）
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 同一份文档里，第几段不能重复（防止重复入库）
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
    )
