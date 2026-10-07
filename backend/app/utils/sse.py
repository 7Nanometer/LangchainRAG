# -*- coding: utf-8 -*-
"""
SSE（Server-Sent Events）工具 —— 服务端"打字机"的传输格式

SSE 是一种网页标准：服务器可以持续不断地往浏览器推送小消息，
用来实现"答案一个字一个字蹦出来"的效果。

格式约定（每个消息以空行结束）：
    event: 事件名
    data: JSON数据
    （空行）
"""
import json


def sse_event(event: str, data) -> str:
    """格式化一个 SSE 事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_comment(text: str = "ping") -> str:
    """
    心跳注释（以冒号开头的行为注释，浏览器会忽略）。
    长时间没有内容输出时发一条，防止网络中间设备把空闲连接掐断。
    """
    return f": {text}\n\n"
