# -*- coding: utf-8 -*-
"""数据看板接口（仅管理员）：总览 / 提问趋势 / 被引用排行 / 未命中清单 / 系统状态"""
import json
import logging
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Chunk, Conversation, Document, Message, User
from ..services import queue_worker, vectorstore
from ..services.embeddings import model_status as embedding_status
from ..services.reranker import model_status as reranker_status

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/stats",
    tags=["数据看板"],
    dependencies=[Depends(require_admin)],
)

# 服务启动时间（由 main.py 在启动时写入，用于展示运行时长）
app_start_time: datetime | None = None


def _today_start() -> datetime:
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def _count(db: Session, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    for cond in conditions:
        stmt = stmt.where(cond)
    return db.scalar(stmt) or 0


@router.get("/overview", summary="看板总览")
def overview(db: Session = Depends(get_db)):
    today = _today_start()
    week_ago = today - timedelta(days=6)

    question_total = _count(db, Message, Message.role == "user")
    assistant_total = _count(db, Message, Message.role == "assistant")
    likes = _count(db, Message, Message.feedback == "like")
    dislikes = _count(db, Message, Message.feedback == "dislike")
    cache_hits = _count(db, Message, Message.role == "assistant", Message.from_cache == 1)
    fallbacks = _count(db, Message, Message.role == "assistant", Message.is_fallback == 1)
    avg_latency = db.scalar(
        select(func.avg(Message.latency_ms)).where(
            Message.role == "assistant", Message.latency_ms > 0
        )
    ) or 0

    return {
        "user_count": _count(db, User),
        "conversation_count": _count(db, Conversation, Conversation.is_deleted == 0),
        "message_count": _count(db, Message),
        "document_count": _count(db, Document),
        "chunk_count": _count(db, Chunk),
        "question_total": question_total,
        "questions_today": _count(db, Message, Message.role == "user", Message.created_at >= today),
        "questions_week": _count(db, Message, Message.role == "user", Message.created_at >= week_ago),
        "likes": likes,
        "dislikes": dislikes,
        "cache_hit_rate": round(cache_hits / assistant_total, 4) if assistant_total else 0.0,
        "fallback_rate": round(fallbacks / assistant_total, 4) if assistant_total else 0.0,
        "avg_latency_ms": int(avg_latency),
    }


@router.get("/trend", summary="每日提问量趋势")
def trend(days: int = 14, db: Session = Depends(get_db)):
    days = max(1, min(days, 90))
    start = _today_start() - timedelta(days=days - 1)
    rows = db.execute(
        select(func.date(Message.created_at), func.count())
        .where(Message.role == "user", Message.created_at >= start)
        .group_by(func.date(Message.created_at))
    ).all()
    counts = {str(day): count for day, count in rows}

    result = []
    for i in range(days):
        day = start + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        result.append({"date": key, "count": counts.get(key, 0)})
    return result


@router.get("/top-documents", summary="被引用最多的资料排行")
def top_documents(days: int = 30, limit: int = 10, db: Session = Depends(get_db)):
    start = datetime.now() - timedelta(days=days)
    citations_list = db.scalars(
        select(Message.citations_json).where(
            Message.role == "assistant",
            Message.created_at >= start,
            Message.citations_json != "[]",
        )
    ).all()

    counter: Counter = Counter()
    for raw in citations_list:
        try:
            for item in json.loads(raw or "[]"):
                name = item.get("filename")
                if name:
                    counter[name] += 1
        except (ValueError, TypeError):
            continue

    return [{"filename": name, "count": n} for name, n in counter.most_common(limit)]


@router.get("/unanswered", summary="未命中问题清单")
def unanswered(limit: int = 30, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    fallback_msgs = db.scalars(
        select(Message)
        .where(Message.role == "assistant", Message.is_fallback == 1)
        .order_by(Message.id.desc())
        .limit(limit)
    ).all()

    result = []
    for msg in fallback_msgs:
        question = db.scalar(
            select(Message.content)
            .where(
                Message.conversation_id == msg.conversation_id,
                Message.role == "user",
                Message.id < msg.id,
            )
            .order_by(Message.id.desc())
            .limit(1)
        )
        result.append(
            {
                "question": question or "（未找到对应提问）",
                "time": msg.created_at,
            }
        )
    return result


@router.get("/system", summary="系统实时状态")
def system():
    uptime_seconds = 0
    if app_start_time is not None:
        uptime_seconds = int((datetime.now() - app_start_time).total_seconds())
    return {
        "embedding_model": dict(embedding_status),
        "reranker_model": dict(reranker_status),
        "vector_count": vectorstore.total_count(),
        "queue_size": queue_worker.queue_size(),
        "processing_document_id": queue_worker.current_document_id(),
        "uptime_seconds": uptime_seconds,
    }
