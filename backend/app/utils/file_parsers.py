# -*- coding: utf-8 -*-
"""
文档解析 —— 把 6 种格式的文件"读成纯文字"

支持格式：
  pdf   → pypdf 逐页提取
  docx  → python-docx（含表格）
  xlsx  → openpyxl（每个工作表逐行转文字）
  csv   → 内置模块（自动识别 UTF-8 / GBK 编码）
  txt   → 文本文件（自动识别编码）
  md    → Markdown（按文本读）

统一输出：一个字符串（纯文本），后续交给"分块 → 向量化"流水线。
"""
import csv
import io
import logging
from pathlib import Path

from ..core.exceptions import AppException

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {"pdf", "docx", "xlsx", "csv", "txt", "md"}


def parse_file(path: Path, file_type: str) -> str:
    """按文件类型解析出纯文本；解析不出内容时抛中文错误"""
    file_type = file_type.lower()
    try:
        if file_type == "pdf":
            text = _parse_pdf(path)
        elif file_type == "docx":
            text = _parse_docx(path)
        elif file_type == "xlsx":
            text = _parse_xlsx(path)
        elif file_type == "csv":
            text = _parse_csv(path)
        elif file_type in ("txt", "md"):
            text = _read_text_auto(path)
        else:
            raise AppException(f"暂不支持的文件格式：{file_type}")
    except AppException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("解析文件失败：%s", path.name)
        raise AppException(f"解析文件失败（{path.name}）：{exc}") from exc

    if len(text.strip()) < 10:
        raise AppException(
            f"从 {path.name} 中提取到的文字太少。如果这是扫描版的 PDF/图片文档，请换成文字版后重新上传"
        )
    return text


def _parse_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        content = page.extract_text() or ""
        if content.strip():
            pages.append(f"（第 {i} 页）\n{content.strip()}")
    return "\n\n".join(pages)


def _parse_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())
    # 表格：每行转成 "列名：值" 的形式（AI 更容易理解）
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _parse_xlsx(path: Path) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(str(path), read_only=True, data_only=True)
    parts: list[str] = []
    for sheet in wb.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        parts.append(f"【工作表：{sheet.title}】")
        header = [str(c).strip() if c is not None else "" for c in rows[0]]
        for row in rows[1:]:
            values = ["" if c is None else str(c).strip() for c in row]
            if not any(values):
                continue
            # 转成「列名：值；列名：值」的自然语言形式
            pairs = [
                f"{header[i]}：{values[i]}"
                for i in range(min(len(header), len(values)))
                if values[i] and header[i]
            ]
            if pairs:
                parts.append("；".join(pairs))
    wb.close()
    return "\n".join(parts)


def _parse_csv(path: Path) -> str:
    text = _read_text_auto(path)
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return ""
    header = [c.strip() for c in rows[0]]
    parts: list[str] = []
    for row in rows[1:]:
        pairs = [
            f"{header[i]}：{row[i].strip()}"
            for i in range(min(len(header), len(row)))
            if i < len(header) and row[i].strip()
        ]
        if pairs:
            parts.append("；".join(pairs))
    return "\n".join(parts)


def _read_text_auto(path: Path) -> str:
    """自动识别编码读文本（先 UTF-8，再 GBK——中文 Windows 常见两种编码）"""
    raw = path.read_bytes()
    for encoding in ("utf-8", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    # 都不行就用 UTF-8 强行解码（忽略坏字符）
    return raw.decode("utf-8", errors="ignore")
