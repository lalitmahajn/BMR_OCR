from pydantic import BaseModel, Field
from typing import List, Optional


class ProductionRow(BaseModel):
    """A single row in the production report table."""

    sr_no: Optional[int] = Field(
        None, description="Serial number of the production entry"
    )
    product_name: Optional[str] = Field(
        None,
        description="Name/code of the manufactured product (e.g., 'RL-5065', 'RL-2028')",
    )
    batch_number: Optional[str] = Field(
        None, description="Batch number for this production run"
    )
    batch_size: Optional[str] = Field(
        None, description="Planned batch size in Kgs (e.g., '6000')"
    )
    quantity_produced: Optional[str] = Field(
        None, description="Actual quantity produced in Kgs (e.g., '5900')"
    )
    packing_details: Optional[str] = Field(
        None,
        description="Packing/mixing/hold details and any additional notes for this row",
    )


class ProductionReportSchema(BaseModel):
    """Structured data extracted from a Production Report page."""

    production_date: Optional[str] = Field(
        None,
        description="The production date, typically shown as 'D+' followed by a date string",
    )
    production_rows: List[ProductionRow] = Field(
        default_factory=list,
        description="All rows from the production table listing products manufactured",
    )
    prepared_by: Optional[str] = Field(
        None, description="Name or signature of the person who prepared the report"
    )
    prepared_by_role: Optional[str] = Field(
        "Production Supervisor",
        description="Role of the person who prepared the report",
    )
    reviewed_by: Optional[str] = Field(
        None, description="Name or signature of the person who reviewed the report"
    )
    reviewed_by_role: Optional[str] = Field(
        "Production Manager",
        description="Role of the person who reviewed the report",
    )
    form_no: Optional[str] = Field(
        None,
        description="Form number printed at the bottom (e.g., 'QAD / RJ / DP-07 / F / 002')",
    )
