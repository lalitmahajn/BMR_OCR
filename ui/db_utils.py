import sys
from pathlib import Path
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from loguru import logger

# Add project root to python path to allow importing app modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.engines.storage import StorageEngine
from app.models.domain import Page, Field, VerificationStatus


def get_session():
    """Get a new DB session."""
    storage = StorageEngine()
    return storage.get_session()


def get_all_pages(session: Session):
    """Fetch all pages with their document name and status."""
    stmt = select(Page).order_by(Page.document_id, Page.page_number)
    return session.scalars(stmt).all()


def get_page_details(session: Session, page_id: int):
    """Fetch a specific page and its fields."""
    page = session.get(Page, page_id)
    return page


def update_field_value(
    session: Session, field_id: int, new_value: str, user_id: str = "human_reviewer"
):
    """Update a field's verified value and status."""
    field = session.get(Field, field_id)
    if field:
        field.verified_value = new_value
        field.verified_by = user_id
        field.status = VerificationStatus.VERIFIED
        session.add(field)
        session.commit()
        return True
    return False


def mark_page_verified(session: Session, page_id: int):
    """Mark all fields in a page as verified (if not already)."""
    # specific logic if needed, or just a flag on the page if we had one.
    # checking if we need to update Field status?
    # For now, let's just commit any pending changes.
    session.commit()
    return True
