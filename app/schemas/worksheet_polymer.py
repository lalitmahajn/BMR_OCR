from typing import Optional, Literal
from pydantic import BaseModel, Field


class GenericTestRow(BaseModel):
    """Standard test result row with the observation and compliance checkmark."""

    results: Optional[str] = Field(
        None, description="The handwritten result/observation"
    )
    complies: Optional[bool] = Field(
        None, description="True if tick is over 'Complies'"
    )


class PolymerIonicity(BaseModel):
    results: Optional[Literal["Cationic", "Anionic", "Non-ionic"]] = Field(
        None, description="The specific option that was ticked"
    )
    complies: Optional[bool] = Field(None)


class Page3Tests(BaseModel):
    """Fields specifically printed on Page 3 (Worksheet Page 1)"""

    physical_appearance: Optional[GenericTestRow] = Field(None)
    viscosity: Optional[GenericTestRow] = Field(None)
    ph: Optional[GenericTestRow] = Field(None)
    specific_gravity: Optional[GenericTestRow] = Field(None)
    solubility: Optional[GenericTestRow] = Field(None)
    ionicity: Optional[PolymerIonicity] = Field(None)
    turbidity: Optional[GenericTestRow] = Field(None)


class SolidContent(BaseModel):
    dish_1_sc_percentage: Optional[str] = Field(None, description="SC % for Dish 1")
    dish_2_sc_percentage: Optional[str] = Field(None, description="SC % for Dish 2")
    solid_content_avg_percentage: Optional[str] = Field(
        None, description="Avg % from the Solid Content test block"
    )


class StabilityRow(BaseModel):
    hours: Optional[str] = Field(
        None, description="Time interval (e.g., Initial, 32 h)"
    )
    ph: Optional[str] = Field(None, description="pH value")
    viscosity: Optional[str] = Field(None, description="Viscosity value")


class StabilityBlock(BaseModel):
    initial: Optional[StabilityRow] = Field(None, description="Pre-printed Initial row")
    row_2: Optional[StabilityRow] = Field(
        None, description="Second handwritten row (e.g. 32 h)"
    )
    row_3: Optional[StabilityRow] = Field(None, description="Third handwritten row")
    row_4: Optional[StabilityRow] = Field(None, description="Fourth handwritten row")


class Page4Tests(BaseModel):
    """Fields specifically printed on Page 4 (Worksheet Page 2)"""

    charge: Optional[GenericTestRow] = Field(None)
    solid_content: Optional[SolidContent] = Field(
        None, description="Dish 1 and Dish 2 solid content results"
    )
    stability: Optional[StabilityBlock] = Field(None, description="3x5 Stability table")


class Page5Tests(BaseModel):
    """Fields specifically printed on Page 5 (Worksheet Page 3)"""

    presence_of_grains_gel: Optional[GenericTestRow] = Field(None)
    wet_strength: Optional[GenericTestRow] = Field(None)


class PolymerWorksheetSchema(BaseModel):
    """Schema native extractor for Polymer Worksheet, matching the constant table specifications."""

    # Header Fields
    document_no: Optional[str] = Field(None)
    revision_no: Optional[float] = Field(None)
    effective_date: Optional[str] = Field(None)
    next_revision_due: Optional[str] = Field(None)

    # Data Sheet Fields
    product_code: Optional[str] = Field(None)
    ar_no: Optional[str] = Field(None)
    batch_no: Optional[str] = Field(None)
    no_of_containers_packs: Optional[str] = Field(None, alias="no_of_containers/packs")
    batch_quantity: Optional[float] = Field(None)
    sampled_quantity: Optional[float] = Field(None)

    solid_content_complies: Optional[bool] = Field(
        None, description="Checkmark overall compliance for Solid Content"
    )
    sampling_date: Optional[str] = Field(None)
    date_of_analysis: Optional[str] = Field(None)
    release_date: Optional[str] = Field(None)

    # Page-Specific Test Blocks
    page_3_tests: Optional[Page3Tests] = Field(
        None, description="Tests on Worksheet Page 1"
    )
    page_4_tests: Optional[Page4Tests] = Field(
        None, description="Tests on Worksheet Page 2"
    )
    page_5_tests: Optional[Page5Tests] = Field(
        None, description="Tests on Worksheet Page 3"
    )

    # Footer Signatures
    analyzed_by: Optional[str] = Field(None)
    checked_by: Optional[str] = Field(None)
    approved_by: Optional[str] = Field(None)
