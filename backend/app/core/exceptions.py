# -*- coding: utf-8 -*-
"""
统一错误处理 —— 保证用户看到的永远是中文人话

无论后端发生什么意外（参数不对、文件坏了、AI 服务连不上……），
前端收到的都是 {code: 数字, message: "中文说明"} 这种统一格式，
不会甩出一堆看不懂的英文报错。
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppException(Exception):
    """业务异常：代码里主动抛出、给用户看的错误（消息必须是中文人话）"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """把所有异常处理器注册到 FastAPI 应用上（在 main.py 启动时调用）"""

    @app.exception_handler(AppException)
    async def _app_exception(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": exc.message},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_request: Request, exc: StarletteHTTPException):
        # 比如访问了不存在的接口
        detail = exc.detail if isinstance(exc.detail, str) and exc.detail else "请求的地址不存在"
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": detail},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception(_request: Request, exc: RequestValidationError):
        # 把程序的英文格式报错，翻译成用户能看懂的提示
        errors = exc.errors()
        message = "填写的内容不符合要求，请检查后重试"
        if errors:
            first = errors[0]
            raw_msg = str(first.get("msg", "")).removeprefix("Value error, ").strip()
            # 我们自己写的校验规则给的是中文提示，直接展示给用户
            if any("一" <= ch <= "鿿" for ch in raw_msg):
                message = raw_msg
            else:
                field = ".".join(str(x) for x in first.get("loc", []) if x != "body") or "输入内容"
                message = f"填写的内容不符合要求（{field}），请检查后重试"
        return JSONResponse(status_code=422, content={"code": 422, "message": message})

    @app.exception_handler(Exception)
    async def _any_exception(request: Request, exc: Exception):
        # 兜底：想不到的意外也统一成中文提示，同时把详细错误写进日志供排查
        logger.exception("未处理异常：%s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器开小差了，请稍后再试（详情可查看日志）"},
        )
