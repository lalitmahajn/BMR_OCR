from pydantic import BaseModel, Field
from typing import List, Optional


class RequisitionItemRow(BaseModel):
    """A single row in the stores requisition items table."""

    sr_no: Optional[int] = Field(
        None, description="Serial number of the item"
    )
    particulars: Optional[str] = Field(
        None,
        description="Name or code of the material requested (e.g., 'R19063', 'HCL', 'IBC Tank', '50 Kg. Carboy')",
    )
    qty_required: Optional[str] = Field(
        None, description="Quantity required in Kgs (e.g., '2144 kg')"
    )
    issued_qty: Optional[str] = Field(
        None, description="Quantity actually issued in Kgs"
    )
    supplier_lot_imi_ar_no: Optional[str] = Field(
        None,
        description="Suppliers Lot No. / IMI No. / A.R. No. for traceability",
    )
    remarks: Optional[str] = Field(
        None, description="Any additional remarks for this item"
    )


class StoresRequisitionSchema(BaseModel):
    """Structured data extracted from a Stores Requisition Slip."""

    batch_no: Optional[str] = Field(
        None,
        description="Batch number, may appear as 'B. No.' (e.g., '10012601674')",
    )
    date: Optional[str] = Field(
        None, description="Date of the requisition (DD/MM/YYYY)"
    )
    product_name: Optional[str] = Field(
        None,
        description="Name or code of the product being manufactured (e.g., 'R10065')",
    )
    batch_capacity: Optional[str] = Field(
        None, description="Batch capacity in Kgs (e.g., '6000 Kgs.')"
    )
    items: List[RequisitionItemRow] = Field(
        default_factory=list,
        description="All rows from the requisition table listing materials requested and issued",
    )
    issued_by: Optional[str] = Field(
        None, description="Name or signature of the person who issued the materials"
    )
    issued_by_date: Optional[str] = Field(
        None, description="Date of issuance"
    )
    production_incharge: Optional[str] = Field(
        None,
        description="Name or signature of the Production In-charge / Executive",
    )
    received_by: Optional[str] = Field(
        None, description="Name or signature of the person who received the materials"
    )
    form_no: Optional[str] = Field(
        None, description="Form number (e.g., 'SR-20-08,Rev:00')"
    )
