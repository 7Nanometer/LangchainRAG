# -*- coding: utf-8 -*-
"""用户表：存账号信息"""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    # 注意：这里存的是加密后的乱码（bcrypt），永远不存明文密码
    password_hash: Mapped[str] = mapped_column(String(128))
    # 角色：admin = 管理员（能管知识库）｜user = 普通用户（只能问答）
    role: Mapped[str] = mapped_column(String(16), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
