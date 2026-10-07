# -*- coding: utf-8 -*-
"""
服务入口 —— 双击「4-启动系统.bat」后，运行的就是本文件

职责：
  1. 启动时：建数据库表、自动创建管理员、打印启动日志
  2. 运行中：接收浏览器请求 → 转给对应接口 → 统一记录请求耗时
  3. 托管前端网页：把「3-构建前端.bat」打包好的网页从这里发出去
     （所以日常使用只需要启动这一个服务，浏览器打开 http://127.0.0.1:8000）
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import api_router
from .config import FRONTEND_DIST, settings
from .core.exceptions import register_exception_handlers
from .core.logging import setup_logging
from .database import Base, SessionLocal, engine
from .services.auth_service import ensure_admin
from .services.embeddings import warm_up_async
from .services.queue_worker import recover_pending_tasks, start_worker

# 让 models 里的表定义全部注册进 Base（create_all 才能建全表）
from . import models  # noqa: F401

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """服务启动前 / 停止后要做的事"""
    # ---- 启动 ----
    Base.metadata.create_all(bind=engine)      # 数据表不存在则自动创建
    with SessionLocal() as db:
        ensure_admin(db)                       # 确保管理员账号存在
    # 启动入库流水线：先恢复上次未完成的任务（重启不丢任务），再开启后台处理队列
    start_worker()
    recover_pending_tasks()
    # 后台预热向量模型（不阻塞启动；预热完成前，第一次上传处理会稍慢）
    warm_up_async()
    logger.info("=" * 56)
    logger.info(" LangchainRAG 知识库问答系统已启动")
    logger.info(" 浏览器访问：http://%s:%s", settings.host, settings.port)
    logger.info("=" * 56)
    yield
    # ---- 停止 ----
    logger.info("服务已停止")


app = FastAPI(title="LangchainRAG 知识库问答系统", lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录每个请求的耗时（写进日志，方便排查慢接口）"""
    start = time.perf_counter()
    response = await call_next(request)
    cost_ms = (time.perf_counter() - start) * 1000
    # 静态资源（图片/js/css）太多不记，只记接口请求
    if not request.url.path.startswith(("/assets", "/favicon")):
        logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, cost_ms)
    return response


# 开发模式跨域支持（前端热更新服务 5173 直连后端时使用；正式使用同源，用不到）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)   # 统一中文错误
app.include_router(api_router)     # 业务接口（/api/...）


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    """探活接口：返回 ok 说明服务活着"""
    return {"status": "ok", "service": "LangchainRAG"}


# ---------------- 前端网页托管 ----------------
# 前端打包产物存在时（跑过「3-构建前端.bat」），由后端直接托管网页
if FRONTEND_DIST.exists():
    _assets_dir = FRONTEND_DIST / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """
        网页兜底路由：
          - 访问 /api/xxx 的请求不走这里（交给上面的接口或 404）
          - 其它路径：能找到对应文件就发文件，找不到就发 index.html
            （这样浏览器里刷新 /chat 这类页面也不会 404）
        """
        if full_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="接口不存在")
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

    logger.info("已启用前端托管：%s", FRONTEND_DIST)
else:
    logger.info("前端尚未构建（跑「3-构建前端.bat」后即可通过本服务访问网页）")


if __name__ == "__main__":
    import uvicorn

    # 注意：必须是单 worker（Chroma 向量库不支持多进程同时写）
    uvicorn.run(app, host=settings.host, port=settings.port, workers=1)
