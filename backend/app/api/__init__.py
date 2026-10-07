# -*- coding: utf-8 -*-
"""接口路由汇总：全部接口统一挂在 /api 前缀下"""
from fastapi import APIRouter

from . import auth

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)

# 后续里程碑会在这里继续注册：
#   conversations（会话管理）、messages（反馈）、chat（流式问答）、admin_*（管理后台）
