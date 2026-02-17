from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from loguru import logger
from fastapi.responses import FileResponse
from pathlib import Path

from app.engines.storage import StorageEngine
from app.models.domain import Document, Page, Field, VerificationStatus
from app.schemas.verification import (
    DocumentResponse,
    PageResponse,
    FieldResponse,
    FieldUpdate,
)

router = APIRouter(prefix="/api/verification", tags=["Verification"])


def get_session():
    storage = StorageEngine()
    session = storage.get_session()
    try:
        yield session
    finally:
        session.close()


@router.get("/documents", response_model=List[DocumentResponse])
def get_documents(session: Session = Depends(get_session)):
    """List all processed documents with status summary."""
    docs = session.scalars(select(Document).order_by(Document.id.desc())).all()
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            ingested_at=d.ingested_at or datetime.now(),
            status=d.status,
            page_count=len(d.pages),
        )
        for d in docs
    ]


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        ingested_at=doc.ingested_at or datetime.now(),
        status=doc.status,
        page_count=len(doc.pages),
    )


@router.get("/documents/{doc_id}/pages", response_model=List[PageResponse])
def get_pages(doc_id: int, session: Session = Depends(get_session)):
    """Get pages for a document."""
    pages = session.scalars(
        select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
    ).all()
    return [
        PageResponse(
            id=p.id,
            page_number=p.page_number,
            image_url=f"/api/verification/images/{p.id}",
            status="processed",
        )
        for p in pages
    ]


@router.get("/pages/{page_id}/fields", response_model=List[FieldResponse])
def get_page_fields(page_id: int, session: Session = Depends(get_session)):
    """Get fields for a specific page."""
    fields = session.scalars(
        select(Field).where(Field.page_id == page_id).order_by(Field.id)
    ).all()
    return [
        FieldResponse(
            id=f.id,
            name=f.name,
            value=f.verified_value if f.verified_value is not None else f.ocr_value,
            confidence=f.ocr_confidence,
            confidence_level=f.confidence_level.value,
            status=f.status.value,
            roi=f.roi_coordinates,
        )
        for f in fields
    ]


@router.patch("/fields/{field_id}", response_model=FieldResponse)
def update_field(
    field_id: int, update: FieldUpdate, session: Session = Depends(get_session)
):
    """Update field value and mark as verified."""
    field = session.get(Field, field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    field.verified_value = update.value
    field.status = VerificationStatus.VERIFIED
    field.verified_by = "user"  # TODO: Add user auth
    session.commit()
    session.refresh(field)

    return FieldResponse(
        id=field.id,
        name=field.name,
        value=field.verified_value,
        confidence=field.ocr_confidence,
        confidence_level=field.confidence_level.value,
        status=field.status.value,
        roi=field.roi_coordinates,
    )


@router.get("/images/{page_id}")
def get_page_image(page_id: int, session: Session = Depends(get_session)):
    """Serve the page image safely."""
    page = session.get(Page, page_id)
    if not page or not page.image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    img_path = Path(page.image_path)
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")

    return FileResponse(img_path)
