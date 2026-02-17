from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"  # OCR done, waiting human
    VERIFIED = "VERIFIED"  # Human confirmed
    FLAGGED = "FLAGGED"  # Needs expert review


class ConfidenceLevel(str, enum.Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, index=True)
    file_hash: Mapped[str] = mapped_column(String, index=True, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(
        String, default="PROCESSING"
    )  # PROCESSING, COMPLETED, ARCHIVED

    pages: Mapped[List["Page"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    image_path: Mapped[str] = mapped_column(String)  # Path to the image on disk
    page_type: Mapped[str] = mapped_column(
        String, nullable=True
    )  # e.g., "BMR_HEADER", "CHECKLIST"
    sub_page_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="pages")
    fields: Mapped[List["Field"]] = relationship(
        back_populates="page", cascade="all, delete-orphan"
    )


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))

    name: Mapped[str] = mapped_column(String)  # Field name from template
    roi_coordinates: Mapped[str] = mapped_column(
        String
    )  # JSON string or specific format x,y,w,h

    ocr_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Raw OCR value
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    verified_value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Human correct value
    verified_by: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # User ID/Name
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel), default=ConfidenceLevel.RED
    )

    page: Mapped["Page"] = relationship(back_populates="fields")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="field")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"))

    previous_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[str] = mapped_column(String)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    reason: Mapped[Optional[str]] = mapped_column(String)

    field: Mapped["Field"] = relationship(back_populates="audit_logs")
