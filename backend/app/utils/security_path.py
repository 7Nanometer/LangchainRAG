# -*- coding: utf-8 -*-
"""上传安全 —— 校验文件类型/大小，生成安全的保存文件名"""
import uuid
from pathlib import Path

from ..config import settings
from ..core.exceptions import AppException
from .file_parsers import SUPPORTED_EXTENSIONS


def validate_upload(filename: str, size_bytes: int) -> str:
    """
    校验上传的文件，返回规范化的扩展名（如 pdf）。
    不合格时抛出中文错误。
    """
    if not filename:
        raise AppException("文件名不能为空")

    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in SUPPORTED_EXTENSIONS:
        allowed = "、".join(sorted(SUPPORTED_EXTENSIONS))
        raise AppException(f"不支持的文件格式（.{ext}）。支持的格式：{allowed}")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise AppException(
            f"文件超过 {settings.max_upload_mb}MB 上限（{filename}），请拆分后再上传"
        )
    if size_bytes == 0:
        raise AppException(f"文件是空的（{filename}）")

    return ext


def make_safe_filename(original_name: str) -> str:
    """
    生成服务器上的保存文件名：随机 ID + 原扩展名。
    这样做的原因：防止"恶意文件名"攻击（路径穿越 / 特殊字符），也避免重名覆盖。
    """
    ext = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"
