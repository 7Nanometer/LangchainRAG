# -*- coding: utf-8 -*-
"""
简单限流 —— 防止有人刷接口把 API 账单刷爆

规则：每个用户每分钟最多提问 N 次（N 在 .env 里配，默认 20）。
实现：内存里记录每人最近一分钟的提问时间，超了就客气地拒绝。
"""
import threading
import time
from collections import defaultdict, deque

from ..config import settings
from .exceptions import AppException

_lock = threading.Lock()
_records: dict[int, deque] = defaultdict(deque)


def check_rate_limit(user_id: int) -> None:
    """检查并记录一次提问；超限时抛出中文错误"""
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return

    now = time.time()
    with _lock:
        queue = _records[user_id]
        # 清掉 1 分钟前的记录
        while queue and now - queue[0] > 60:
            queue.popleft()
        if len(queue) >= limit:
            wait_seconds = int(60 - (now - queue[0])) + 1
            raise AppException(f"提问太频繁啦，请等 {wait_seconds} 秒后再试", 429)
        queue.append(now)
