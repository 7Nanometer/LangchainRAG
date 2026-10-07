# -*- coding: utf-8 -*-
"""消息表：对话里的每一句话（用户问的 + AI 答的）"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    # 角色：user = 用户发的 ｜ assistant = AI 答的
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text, default="")

    # 引用快照：AI 回答时参考了哪些资料片段（存 JSON 文本）。
    # 存"快照"而不是引用关系的原因：之后资料即使被改/删，历史记录里的引用依旧能看到原样
    citations_json: Mapped[str] = mapped_column(Text, default="[]")

    # 用户反馈：like = 点赞 ｜ dislike = 点踩 ｜ NULL = 未评价
    feedback: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # 是否兜底回答（资料里没找到，AI 说"不知道"）——看板的"未命中清单"用它统计
    is_fallback: Mapped[int] = mapped_column(Integer, default=0)
    # 是否直接命中了缓存（秒回的答案）
    from_cache: Mapped[int] = mapped_column(Integer, default=0)
    # 本条回答耗时（毫秒）——看板算平均响应速度
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    # 多轮追问改写后的完整问题（比如"它多少钱"→"W1耳机多少钱"），排查检索问题用
    rewritten_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
