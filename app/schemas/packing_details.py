from pydantic import BaseModel, Field
from typing import List, Optional


class DrumRow(BaseModel):
    """A single row in the packing details drum table."""

    drum_no: Optional[str] = Field(
        None, description="Drum number or identifier"
    )
    gross_weight: Optional[str] = Field(
        None, description="Gross weight of the drum"
    )
    done_by: Optional[str] = Field(
        None, description="Person who weighed/packed"
    )
    checked_by: Optional[str] = Field(
        None, description="Person who verified the weight"
    )


class PackingDetailsSchema(BaseModel):
    """Structured data extracted from a Packing Details form."""

    product_name: Optional[str] = Field(
        None, description="Name of the product"
    )
    batch_no: Optional[str] = Field(
        None, description="Batch number (e.g., '10012601674')"
    )
    total_qty: Optional[str] = Field(
        None, description="Total quantity"
    )
    tare_weight: Optional[str] = Field(
        None, description="Tare weight of containers"
    )
    balance_id: Optional[str] = Field(
        None, description="Balance ID number used for weighing"
    )
    calibration_status: Optional[str] = Field(
        None, description="Calibration status of the balance"
    )
    rinsing_status: Optional[str] = Field(
        None,
        description="Whether all containers were rinsed (Yes/No)",
    )
    signature_and_date: Optional[str] = Field(
        None, description="Signature and date of the responsible person"
    )
    drums: List[DrumRow] = Field(
        default_factory=list,
        description="All rows from the drum packing table",
    )
    page_info: Optional[str] = Field(
        None, description="Page number info (e.g., 'Page No.-1 of 2')"
    )
