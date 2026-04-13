from pydantic import BaseModel, Field
from typing import List, Optional


class VoucherItemRow(BaseModel):
    """A single row in the issue voucher items table."""

    item_name: Optional[str] = Field(
        None,
        description="Name or code of the material item (e.g., '9063', '7028', '7110')",
    )
    godown: Optional[str] = Field(
        None,
        description="Storage location / godown name (e.g., 'Finished Goods - Approved', 'Raw Material G 3 - Approved')",
    )
    batch_lot: Optional[str] = Field(
        None,
        description="Batch or lot reference including dates if present (e.g., '10012601614 12/01/2026 11/01/2027')",
    )
    quantity: Optional[str] = Field(
        None,
        description="Quantity issued with unit (e.g., '244.000 Kgs', '0.490 Kgs')",
    )


class IssueVoucherSchema(BaseModel):
    """Structured data extracted from an Issue - Material Voucher."""

    voucher_no: Optional[str] = Field(
        None,
        description="Voucher number (e.g., '25-26/3578')",
    )
    ref_no: Optional[str] = Field(
        None,
        description="Reference number, usually a batch number (e.g., '10012601674')",
    )
    ref_date: Optional[str] = Field(
        None,
        description="Reference date, shown as 'dt.' (e.g., '21/01/2026')",
    )
    dated: Optional[str] = Field(
        None,
        description="Date of the voucher (e.g., '21/01/2026')",
    )
    items: List[VoucherItemRow] = Field(
        default_factory=list,
        description="All rows from the voucher table listing materials issued",
    )
    total_quantity: Optional[str] = Field(
        None,
        description="Total quantity at the bottom of the table (e.g., '1,624.899 Kgs')",
    )
    narration: Optional[str] = Field(
        None,
        description="Narration text describing the transaction (e.g., '10012601674:RL 5065:BC 6000:Date:21/01/2026')",
    )
    checked_by: Optional[str] = Field(
        None, description="Name or signature of the person who checked"
    )
    checked_by_date: Optional[str] = Field(
        None, description="Date when checked (DD/MM/YYYY)"
    )
    verified_by: Optional[str] = Field(
        None, description="Name or signature of the person who verified"
    )
    verified_by_date: Optional[str] = Field(
        None, description="Date when verified (DD/MM/YYYY)"
    )
    authorised_signatory: Optional[str] = Field(
        None, description="Name or signature of the authorised signatory"
    )
