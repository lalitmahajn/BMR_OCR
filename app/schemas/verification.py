from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    ingested_at: datetime
    status: str
    page_count: int


class PageResponse(BaseModel):
    id: int
    page_number: int
    image_url: str
    status: str


class FieldResponse(BaseModel):
    id: int
    name: str
    value: Optional[str]
    confidence: float
    confidence_level: str
    status: str
    roi: Optional[str]


class FieldUpdate(BaseModel):
    value: str
