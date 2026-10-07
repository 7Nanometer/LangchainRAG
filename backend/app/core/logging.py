# -*- coding: utf-8 -*-
"""
日志系统 —— 系统的"行车记录仪"

同时往两个地方写日志：
  1. 控制台窗口（运行时能直接看到）
  2. backend\data\logs\app.log 文件（出问题时翻查）
日志文件最大 10MB，自动滚动保留最近 5 份，不会无限撑大硬盘。
"""
import logging
from logging.handlers import RotatingFileHandler

from ..config import LOG_DIR

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:  # 已配置过就不重复添加（防止热重载时日志翻倍）
        return

    root.setLevel(logging.INFO)
    formatter = logging.Formatter(_LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 把 uvicorn（网络服务）和第三方库的日志噪声压一压
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
