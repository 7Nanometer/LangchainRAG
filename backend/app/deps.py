# -*- coding: utf-8 -*-
"""
公共依赖 —— 接口的"门禁"

每个需要登录的接口，请求进来时都会先经过这里：
  1. 检查有没有带通行证（JWT）
  2. 通行证是否有效、有没有过期
  3. 换成真实的用户对象

管理接口额外过一道 require_admin —— 普通用户即使绕过前端
直接调接口，也会被拦下来。
"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .core.exceptions import AppException
from .core.security import decode_access_token
from .database import get_db
from .models import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """从请求头里取出通行证，验证后返回当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException("请先登录", 401)

    token = authorization.removeprefix("Bearer ").strip()
    user_id = decode_access_token(token)
    if user_id is None:
        raise AppException("登录已过期，请重新登录", 401)

    user = db.get(User, user_id)
    if user is None:
        raise AppException("账号不存在，请重新登录", 401)
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求当前用户必须是管理员，否则拒绝"""
    if not user.is_admin:
        raise AppException("没有权限执行此操作（仅管理员可用）", 403)
    return user
