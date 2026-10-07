# -*- coding: utf-8 -*-
"""接口路由汇总：全部接口统一挂在 /api 前缀下"""
from fastapi import APIRouter

from . import admin_documents, admin_kb, auth

api_router = APIRouter(prefix="/api")

# 认证（注册/登录/改密）
api_router.include_router(auth.router)
# 知识库管理（仅管理员）
api_router.include_router(admin_kb.router)
# 文档管理（仅管理员）
api_router.include_router(admin_documents.router)

# 后续里程碑会在这里继续注册：
#   conversations（会话管理）、messages（反馈）、chat（流式问答）、admin_stats（看板）
