from pydantic import BaseModel, Field
from typing import List, Optional


class SpecRow(BaseModel):
    """A single row in the product specification table."""

    no: Optional[int] = Field(
        None, description="Row number in the specification table"
    )
    parameter: str = Field(
        description="Name of the test parameter (e.g., 'Viscosity', 'pH', 'Solid Content')"
    )
    factory_specification: Optional[str] = Field(
        None,
        description="Factory specification range (e.g., '30 To 70', '3 To 4')",
    )
    marketing_specification: Optional[str] = Field(
        None,
        description="Marketing specification range (e.g., '20 To 80', '3 To 7')",
    )
    unit: Optional[str] = Field(
        None, description="Unit of measurement (e.g., 'cps', 'NTU', '%', 'N')"
    )
    test_method: Optional[str] = Field(
        None,
        description="Testing method used (e.g., 'Viscometer', 'By pH meter', 'By Charge Analyser')",
    )


class ProductSpecSchema(BaseModel):
    """Structured data extracted from a Product Specification page (ERP screenshot)."""

    product_code: Optional[str] = Field(
        None,
        description="Product code identifier, may include multiple codes separated by >> (e.g., '5065322C >> 5065')",
    )
    shelf_life: Optional[str] = Field(
        None, description="Product shelf life (e.g., '6 Months')"
    )
    spec_rows: List[SpecRow] = Field(
        default_factory=list,
        description="All rows from the specification parameters table",
    )
    special_instructions: Optional[str] = Field(
        None,
        description="Any special instructions noted at the bottom of the spec table",
    )
    batch_no: Optional[str] = Field(
        None,
        description="Batch number if present, may appear as 'B. No:' at the bottom (e.g., '10012601674')",
    )
