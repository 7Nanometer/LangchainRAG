# -*- coding: utf-8 -*-
"""文档管理接口：上传（多文件）/ 列表 / 详情 / 删除 / 重建（仅管理员）"""
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..core.exceptions import AppException
from ..database import get_db
from ..deps import require_admin
from ..models import Document, KnowledgeBase
from ..schemas.admin import DocumentOut
from ..services.ingestion_service import delete_document_data
from ..services.queue_worker import enqueue
from ..utils.security_path import make_safe_filename, validate_upload

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["文档管理"],
    dependencies=[Depends(require_admin)],
)


def _get_doc_or_404(db: Session, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise AppException("文档不存在", 404)
    return doc


@router.get("/kb/{kb_id}/documents", summary="某知识库的文档列表")
def list_documents(
    kb_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    if db.get(KnowledgeBase, kb_id) is None:
        raise AppException("知识库不存在", 404)
    stmt = (
        select(Document)
        .where(Document.kb_id == kb_id)
        .order_by(Document.created_at.desc())
    )
    if status:
        stmt = stmt.where(Document.status == status)
    return [DocumentOut.model_validate(d) for d in db.scalars(stmt)]


@router.post("/kb/{kb_id}/documents", summary="上传文档（可一次多个文件）")
async def upload_documents(
    kb_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    上传后立即返回（不等待解析），后台队列会逐个处理。
    前端通过轮询文档列表看处理进度。
    """
    if db.get(KnowledgeBase, kb_id) is None:
        raise AppException("知识库不存在", 404)

    saved: list[DocumentOut] = []
    errors: list[str] = []

    for f in files:
        try:
            content = await f.read()
            original_name = f.filename or "未命名文件"
            ext = validate_upload(original_name, len(content))

            # 保存原文件（随机文件名，防重名和路径攻击）
            safe_name = make_safe_filename(original_name)
            dest = UPLOAD_DIR / safe_name
            dest.write_bytes(content)

            doc = Document(
                kb_id=kb_id,
                filename=original_name,
                file_path=str(dest),
                file_type=ext,
                size_bytes=len(content),
                status="pending",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            enqueue(doc.id)  # 交给后台队列处理
            saved.append(DocumentOut.model_validate(doc))
            logger.info("已接收上传：%s（%.1fKB）", original_name, len(content) / 1024)
        except AppException as exc:
            errors.append(exc.message)
        except Exception:  # noqa: BLE001
            logger.exception("保存上传文件失败：%s", f.filename)
            errors.append(f"{f.filename}：保存失败，请重试")
        finally:
            await f.close()

    return {"saved": saved, "errors": errors}


@router.get("/documents/{doc_id}", summary="文档详情")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return DocumentOut.model_validate(_get_doc_or_404(db, doc_id))


@router.delete("/documents/{doc_id}", summary="删除文档")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = _get_doc_or_404(db, doc_id)
    name = doc.filename
    delete_document_data(db, doc)
    logger.info("已删除文档：%s", name)
    return {"message": f"文档「{name}」已删除"}


@router.post("/documents/{doc_id}/reindex", summary="重建单个文档的索引")
def reindex_document(doc_id: int, db: Session = Depends(get_db)):
    doc = _get_doc_or_404(db, doc_id)
    doc.status = "pending"
    doc.processed_chunks = 0
    doc.error_msg = None
    db.commit()
    enqueue(doc.id)
    return {"message": f"文档「{doc.filename}」已加入重建队列"}
