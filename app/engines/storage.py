from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import List
from loguru import logger
from datetime import datetime

from app.core.config import settings
from app.models.domain import Document, Page, Field, AuditLog, VerificationStatus


class DatabaseGateError(Exception):
    pass


class StorageEngine:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)

    def get_session(self) -> Session:
        return Session(self.engine)

    def save_pending_document(self, db: Session, document: Document):
        """
        Saves the initial document structure (before verification).
        Status should be PROCESSING or PENDING.
        """
        logger.info(f"Saving pending document: {document.filename}")
        db.add(document)
        db.commit()
        db.refresh(document)

    def commit_verified_data(self, db: Session, field: Field, user_id: str):
        """
        CRITICAL: The only way to finalize data into the DB as 'VERIFIED'.
        Enforces human verification.
        """
        if not user_id:
            raise DatabaseGateError("Cannot commit without a verifier (User ID).")

        field.verified_by = user_id
        field.verified_at = datetime.utcnow()
        field.status = VerificationStatus.VERIFIED

        # Create Audit Log
        audit = AuditLog(
            field_id=field.id,
            changed_by=user_id,
            previous_value=field.ocr_value,  # Simplified for now
            new_value=field.verified_value,
            reason="Human verification",
        )
        db.add(audit)

        db.add(field)
        db.commit()
        logger.info(f"Field {field.name} verified by {user_id}")
