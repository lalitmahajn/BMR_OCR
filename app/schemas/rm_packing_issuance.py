from pydantic import BaseModel, Field
from typing import List, Optional


class IssuanceRow(BaseModel):
    """A single row in the RM/Packing Material issuance table."""

    sr_no: Optional[int] = Field(
        None, description="Serial number"
    )
    raw_material: Optional[str] = Field(
        None,
        description="Raw material code or name (e.g., '7093', '7110', '7599')",
    )
    ar_no: Optional[str] = Field(
        None, description="AR number for this material (e.g., '1108')"
    )
    barrel_carboy_count: Optional[str] = Field(
        None,
        description="Number and type of barrels/carboys (e.g., '3Carboy', 'By Line')",
    )
    barrel_condition: Optional[str] = Field(
        None,
        description="Barrel & Carboy condition — Seal or Damage (e.g., 'OK')",
    )
    labeling: Optional[str] = Field(
        None,
        description="Labeling status on each barrel/carboy with specific weight (e.g., 'OK')",
    )
    bags_count: Optional[str] = Field(
        None, description="Number of bags (e.g., '6bogs', '-')"
    )
    bags_condition: Optional[str] = Field(
        None, description="Bags condition — Seal or Damage (e.g., 'OK', '-')"
    )
    weight_kg: Optional[str] = Field(
        None, description="Weight in Kg (e.g., '1041g', '29203kg')"
    )
    expire_date: Optional[str] = Field(
        None,
        description="Expiry date checked (e.g., 'Sep.27', 'Nov-26', 'Mar-26')",
    )
    physical_appearance: Optional[str] = Field(
        None, description="Physical appearance observation if possible"
    )
    excess_shortage: Optional[str] = Field(
        None, description="Excess/Shortage quantity if any"
    )
    remark: Optional[str] = Field(
        None, description="Any additional remarks"
    )
    prod_rep: Optional[str] = Field(
        None, description="Production representative signature/initials"
    )
    store_rep: Optional[str] = Field(
        None, description="Store representative signature/initials"
    )


class RMPackingIssuanceSchema(BaseModel):
    """Structured data extracted from a Raw Material & Packing Material Issuance Record."""

    document_no: Optional[str] = Field(
        None,
        description="Document number (e.g., 'STR/WI-20-02/F/004')",
    )
    revision_no: Optional[str] = Field(
        None, description="Revision number (e.g., '00')"
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date of the form"
    )
    review_date: Optional[str] = Field(
        None, description="Review date of the form"
    )
    product: Optional[str] = Field(
        None,
        description="Product name or code (e.g., 'RL-SD65')",
    )
    batch_no: Optional[str] = Field(
        None, description="Batch number (e.g., '15012601676')"
    )
    date: Optional[str] = Field(
        None, description="Date of issuance (DD/MM/YYYY)"
    )
    items: List[IssuanceRow] = Field(
        default_factory=list,
        description="All rows from the issuance table listing materials issued",
    )
    prepared_issued_by: Optional[str] = Field(
        None, description="Name/signature of person who prepared and issued"
    )
    prepared_date: Optional[str] = Field(
        None, description="Date of preparation"
    )
    reviewed_by: Optional[str] = Field(
        None, description="Name/signature of reviewer"
    )
    reviewed_date: Optional[str] = Field(
        None, description="Date of review"
    )
    approved_by: Optional[str] = Field(
        None, description="Name/signature of approver"
    )
    approved_date: Optional[str] = Field(
        None, description="Date of approval"
    )
