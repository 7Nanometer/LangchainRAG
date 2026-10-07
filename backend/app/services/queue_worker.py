# -*- coding: utf-8 -*-
"""
入库队列 —— 单线程"流水线工人"

为什么需要它：
  - 上传接口立即返回（用户不用干等），文档在后台排队处理
  - 一次只处理一份：既不会几个任务抢显卡，也不会卡住聊天问答
  - 服务重启时未处理完的文档自动重新排队（不丢任务）

工作方式：管理员上传 → 文档 id 进入队列 → 工人按顺序逐个处理。
"""
import logging
import queue
import threading

from sqlalchemy import select

from ..database import SessionLocal
from ..models import Document
from .ingestion_service import process_document

logger = logging.getLogger(__name__)

_task_queue: "queue.Queue[int]" = queue.Queue()
_worker_thread: threading.Thread | None = None
_current_document_id: int | None = None  # 当前正在处理的文档（状态接口显示用）


def start_worker() -> None:
    """启动流水线工人（服务启动时调用一次）"""
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    _worker_thread = threading.Thread(target=_loop, daemon=True, name="ingest-worker")
    _worker_thread.start()
    logger.info("入库队列已启动")


def enqueue(document_id: int) -> None:
    """把一份文档加入处理队列"""
    _task_queue.put(document_id)
    logger.info("文档 %s 已进入处理队列（当前排队：%s 个）", document_id, _task_queue.qsize())


def queue_size() -> int:
    return _task_queue.qsize()


def current_document_id() -> int | None:
    return _current_document_id


def recover_pending_tasks() -> None:
    """服务启动时：把上次中断的任务重新排队（重启不丢任务）"""
    db = SessionLocal()
    try:
        docs = db.scalars(
            select(Document).where(Document.status.in_(["pending", "processing"]))
        ).all()
        for doc in docs:
            doc.status = "pending"
            doc.processed_chunks = 0
            enqueue(doc.id)
        db.commit()
        if docs:
            logger.info("已恢复 %s 个未完成的入库任务", len(docs))
    finally:
        db.close()


def _loop() -> None:
    """工人主循环：不断从队列取任务执行"""
    global _current_document_id
    while True:
        document_id = _task_queue.get()
        _current_document_id = document_id
        try:
            process_document(document_id)
        except Exception:  # noqa: BLE001 —— 兜底：工人绝不退出
            logger.exception("处理文档 %s 时发生未捕获异常", document_id)
        finally:
            _current_document_id = None
            _task_queue.task_done()
