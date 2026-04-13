from pydantic import BaseModel, Field
from typing import List, Optional


class ReviewPointRow(BaseModel):
    """A single review point in Section A of the BMR Review Checklist."""

    sr_no: Optional[int] = Field(
        None, description="Serial number of the review point"
    )
    review_point: str = Field(
        description="Full text of the review point question"
    )
    status: Optional[str] = Field(
        None,
        description="Status: 'Yes', 'No', or 'NA'. Determined from checkboxes (☑ marks) specifically in Section A on Page 1.",
    )


class AttachmentRow(BaseModel):
    """A single row in Section B (Attachments) of the BMR Review Checklist."""

    sr_no: Optional[int] = Field(
        None, description="Serial number"
    )
    attachment: str = Field(
        description="Name of the attachment (e.g., 'Issuance slip (Voucher)', 'Deviation Report', 'Data Logger', 'QC Test Report')"
    )
    status: Optional[str] = Field(
        None,
        description="Status: 'Yes', 'No', or 'NA'. Determined from checkboxes (☑ marks) specifically in Section B on Page 2.",
    )


class BMRChecklistSchema(BaseModel):
    """Structured data extracted from a BMR Review Checklist (typically 2 pages)."""

    document_no: Optional[str] = Field(
        None, description="Document number (e.g., 'QAD/RJ-DP-02/F/001')"
    )
    revision_no: Optional[str] = Field(
        None, description="Revision number (e.g., '01')"
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date of the checklist form"
    )
    review_date: Optional[str] = Field(
        None, description="Review date of the checklist form"
    )
    # Section A: Review Points
    review_points: List[ReviewPointRow] = Field(
        default_factory=list,
        description="All 15 review points from 'SECTION: - A' on the first page of the checklist.",
    )
    # Section B: Attachments
    attachments: List[AttachmentRow] = Field(
        default_factory=list,
        description="All attachment items from 'SECTION: - B' on the second page of the checklist.",
    )
    # Footer signatures
    prepared_issued_by: Optional[str] = Field(
        None, description="QA Executive who prepared and issued"
    )
    reviewed_by: Optional[str] = Field(
        None, description="Asst. QA Manager who reviewed"
    )
    approved_by: Optional[str] = Field(
        None, description="QA Manager / MR who approved"
    )
