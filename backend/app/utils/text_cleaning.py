# -*- coding: utf-8 -*-
"""文本清洗 —— 把解析出来的文字"捋干净"，提升检索质量"""
import re


def clean_text(text: str) -> str:
    """
    清洗规则（每一条都是为了向量检索更准）：
      1. 统一换行符，去掉零宽字符等不可见字符
      2. 行内连续空格压缩成一个
      3. 连续 3 行以上的空行压缩成 1 个空行
      4. 去掉首尾空白
    """
    if not text:
        return ""
    # 统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 去掉零宽字符 / BOM / 页眉页脚常见控制符
    text = re.sub(r"[​‌‍﻿\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # 行内空格压缩（保留缩进信息就统一压成一个空格）
    text = re.sub(r"[ \t　]+", " ", text)
    # 每行去尾空格
    lines = [line.strip() for line in text.split("\n")]
    # 连续空行压缩
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if line:
            blank_run = 0
            cleaned.append(line)
        else:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()
