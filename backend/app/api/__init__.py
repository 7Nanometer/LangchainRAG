# -*- coding: utf-8 -*-
"""接口路由汇总：全部接口统一挂在 /api 前缀下"""
from fastapi import APIRouter

from . import admin_documents, admin_kb, auth, chat, conversations, messages

api_router = APIRouter(prefix="/api")

# 认证（注册/登录/改密）
api_router.include_router(auth.router)
# 知识库管理（仅管理员）
api_router.include_router(admin_kb.router)
# 文档管理（仅管理员）
api_router.include_router(admin_documents.router)
# 会话管理（登录用户）
api_router.include_router(conversations.router)
# 消息反馈（登录用户）
api_router.include_router(messages.router)
# 流式问答（登录用户）
api_router.include_router(chat.router)

# 后续里程碑会在这里继续注册：admin_stats（数据看板）
