# -*- coding: utf-8 -*-
"""账号业务逻辑：注册、登录验证、改密码、创建管理员"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..core.exceptions import AppException
from ..core.security import hash_password, verify_password
from ..models import User

logger = logging.getLogger(__name__)


def register_user(db: Session, username: str, password: str) -> User:
    """注册新用户（角色固定为普通用户）"""
    exists = db.scalar(select(User).where(User.username == username))
    if exists:
        raise AppException("用户名已被占用，换一个试试")

    user = User(username=username, password_hash=hash_password(password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("新用户注册：%s", username)
    return user


def authenticate(db: Session, username: str, password: str) -> User:
    """登录验证：用户名密码都对才放行"""
    user = db.scalar(select(User).where(User.username == username))
    # 注意：无论"用户不存在"还是"密码错误"，都返回同一句提示（防止攻击者探测哪些用户名存在）
    if user is None or not verify_password(password, user.password_hash):
        raise AppException("用户名或密码错误", 401)
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """修改密码：必须先验证旧密码"""
    if not verify_password(old_password, user.password_hash):
        raise AppException("旧密码不正确")
    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info("用户 %s 修改了密码", user.username)


def ensure_admin(db: Session) -> None:
    """
    确保管理员账号存在（首次启动时自动创建）。
    如果管理员已存在（哪怕改过密码），绝不覆盖 —— 只在"查无此人"时创建。
    密码从 .env 配置读取（不写在代码里）；未配置时跳过并给出警告。
    """
    admin = db.scalar(select(User).where(User.username == settings.admin_username))
    if admin is not None:
        return
    if not settings.admin_password:
        logger.warning(
            "未配置管理员密码（backend\\.env 里的 ADMIN_PASSWORD），跳过管理员创建"
        )
        return
    db.add(
        User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            role="admin",
        )
    )
    db.commit()
    logger.info("已自动创建管理员账号：%s", settings.admin_username)
