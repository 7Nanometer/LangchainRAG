# -*- coding: utf-8 -*-
"""认证接口：注册 / 登录 / 查询当前用户 / 修改密码"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.security import create_access_token
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ChangePasswordRequest, LoginRequest, RegisterRequest, UserOut
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="注册新账号")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, payload.username, payload.password)
    return {"message": "注册成功", "user": UserOut.model_validate(user)}


@router.post("/login", summary="登录，获取通行证")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.username, payload.password)
    token = create_access_token(user.id)
    return {"token": token, "user": UserOut.model_validate(user)}


@router.get("/me", summary="查询当前登录用户")
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/change-password", summary="修改密码")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, user, payload.old_password, payload.new_password)
    return {"message": "密码修改成功，下次请用新密码登录"}
