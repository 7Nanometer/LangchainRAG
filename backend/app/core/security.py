# -*- coding: utf-8 -*-
"""
安全工具 —— 两件大事：

1. 密码加密（bcrypt）
   注册/改密码时，把密码变成一段"无法还原的乱码"再存进数据库。
   就算数据库文件被别人拿到，也看不到原始密码。
   登录时用同样的算法"验算"，一致才算密码正确。

2. 登录通行证（JWT）
   登录成功后发给浏览器一张"电子通行证"（一串加密字符），
   之后每次操作带上它，后端验签就知道"你是谁"，不用反复输密码。
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ..config import get_or_create_secret_key, settings

_ALGORITHM = "HS256"
# 系统内部的"私章"，用来给通行证盖章；第一次启动自动生成并保存
_SECRET_KEY = get_or_create_secret_key()


def hash_password(password: str) -> str:
    """把明文密码变成加密乱码（存数据库用）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码和数据库里的乱码是否匹配"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    """签发通行证：里面有用户 ID 和有效期"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """验证通行证：有效则返回用户 ID，过期或伪造则返回 None"""
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        return int(payload.get("sub", 0))
    except (jwt.PyJWTError, ValueError, TypeError):
        return None
