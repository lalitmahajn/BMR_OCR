from pydantic import BaseModel, Field
from typing import List, Optional


class RecipeRow(BaseModel):
    """A row in the Standard Recipe or Batch Recipe table."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    raw_material_name: Optional[str] = Field(
        None,
        description="Raw material code/name (e.g., '9063', '7048', '7028')",
    )
    qty_kgs: Optional[str] = Field(
        None, description="Quantity in KGS (e.g., '1600', '460.0')"
    )
    recipe_or_solid_percent: Optional[str] = Field(
        None,
        description="Recipe percentage for Standard Recipe OR Solid percentage for Batch Recipe (e.g., '15.84', '7.921')",
    )
    remarks: Optional[str] = Field(
        None, description="Additional remarks (e.g., actual kg values like '950.49 kg')"
    )


class ProductSpecRow(BaseModel):
    """A row in the product specifications table (Section 3.2)."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    parameter: Optional[str] = Field(
        None, description="Parameter name (e.g., 'VISCOSITY', 'pH')"
    )
    specification_limits: Optional[str] = Field(
        None, description="Specification limits (e.g., '30-70 CPS')"
    )


class ResponsibilityRow(BaseModel):
    """A row in the Responsibility table (Section 5)."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    activity: Optional[str] = Field(
        None,
        description="Activity description (e.g., 'Preparation of B.M.R.', 'Checking of B.M.R.')",
    )
    role: Optional[str] = Field(
        None,
        description="Responsible role (e.g., 'Operator/ Supervisor – Production', 'Manager – Q.A.')",
    )


class RevisionHistoryRow(BaseModel):
    """A row in the Revision History table (Section 6)."""

    revision_no: Optional[str] = Field(
        None, description="Revision number (e.g., '00', '01', '02')"
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date of this revision (DD/MM/YYYY)"
    )
    description_of_change: Optional[str] = Field(
        None,
        description="Description of what changed in this revision (e.g., 'NEW SOP', 'Recipe revises for resolving the BNPM')",
    )


class SOPSchema(BaseModel):
    """Structured data extracted from a Standard Operating Procedure (typically 6 pages)."""

    sop_no: Optional[str] = Field(
        None, description="SOP number (e.g., 'SOP/5065')"
    )
    revision: Optional[str] = Field(
        None, description="Revision number (e.g., '02')"
    )
    product_name: Optional[str] = Field(
        None, description="Name of the product (e.g., '5065')"
    )
    effective_date: Optional[str] = Field(
        None, description="Effective date (DD/MM/YYYY)"
    )
    page_info: Optional[str] = Field(
        None, description="Page info (e.g., '01 of 06')"
    )
    # Section 1: Scope
    scope: Optional[str] = Field(
        None,
        description="Scope text describing applicability of the SOP",
    )
    # Section 1.1: Standard Recipe
    standard_recipe: List[RecipeRow] = Field(
        default_factory=list,
        description="Standard Recipe table with raw materials, quantities, and recipe percentages",
    )
    batch_input_capacity: Optional[str] = Field(
        None, description="Batch Input / Theoretical Capacity (e.g., '10100 Kgs')"
    )
    batch_output_yield: Optional[str] = Field(
        None, description="Batch Output / Practical Yield (e.g., '10000 Kgs')"
    )
    yield_range_kgs: Optional[str] = Field(
        None, description="Output Yield Range in Kgs (e.g., '9900 - 10100')"
    )
    yield_range_percent: Optional[str] = Field(
        None, description="Output Yield Range in Percentage (e.g., '98 - 100')"
    )
    # Section 1.2: Batch Recipe
    batch_recipe: List[RecipeRow] = Field(
        default_factory=list,
        description="Batch Recipe table with raw materials, quantities, and solid percentages",
    )
    # Section 2: Pre-Operating Procedure
    important_notes: Optional[str] = Field(
        None, description="Important notes text block (Section 2.1)"
    )
    pre_checks: Optional[str] = Field(
        None, description="Pre-checks text block (Section 2.2)"
    )
    pre_operating_steps: Optional[str] = Field(
        None, description="Pre-operating steps text block (Section 2.3)"
    )
    # Section 3: Batch Operating Procedure
    batch_operating_procedure: Optional[str] = Field(
        None,
        description="Batch operating procedure text block (Section 3.1) with step-by-step instructions",
    )
    # Section 3.2: Product Specifications
    product_specifications: List[ProductSpecRow] = Field(
        default_factory=list,
        description="Aim for product specifications table",
    )
    # Section 4: Packing
    packing_of_material: Optional[str] = Field(
        None, description="Packing of material instructions (Section 4)"
    )
    # Section 5: Responsibility
    responsibility: List[ResponsibilityRow] = Field(
        default_factory=list,
        description="Responsibility table mapping activities to roles (e.g., who prepares, checks, reviews, approves B.M.R.)",
    )
    # Section 6: Revision History
    revision_history: List[RevisionHistoryRow] = Field(
        default_factory=list,
        description="Revision history table showing all past SOP revisions with dates and descriptions of changes",
    )
