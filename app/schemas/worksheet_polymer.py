from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


class WorksheetTestRow(BaseModel):
    sr_no: Optional[int] = Field(None, description="The serial number of the test")
    parameter: str = Field(..., description="Name of the test parameter")
    observation: Optional[str] = Field(None, description="The raw observation or measurement")
    complies: Optional[bool] = Field(None, description="True if the result complies with specifications")


class SolidContentDish(BaseModel):
    dish_id: Optional[str] = Field(None, description="Dish ID")
    weight_empty_dish: Optional[str] = Field(None, description="Weight of empty Dish")
    weight_dish_plus_sample: Optional[str] = Field(None, description="Weight of Dish + Sample")
    weight_sample: Optional[str] = Field(None, description="Weight of sample (X-Y)")
    weight_dried_sample_with_dish: Optional[str] = Field(None, description="Weight of dried Sample with dish (A)")
    net_weight_dried_sample: Optional[str] = Field(None, description="Net weight of dried Sample (C)")
    sc_percentage: Optional[str] = Field(None, description="Calculated Solid Content (SC) percentage")

class SolidContentTest(BaseModel):
    dish_1: Optional[SolidContentDish] = Field(None, description="First dish calculation")
    dish_2: Optional[SolidContentDish] = Field(None, description="Second dish calculation (if any)")
    average_sc_percentage: Optional[str] = Field(None, description="Average Solid Content percentage")
    complies: Optional[bool] = Field(None, description="True if the overall solid content complies")

class StabilityTestRow(BaseModel):
    """Specific sub-table for Stability results at different intervals."""
    interval: str = Field(..., description="Time interval (e.g., Initial, 24 Hrs, 72 Hrs)")
    ph: Optional[str] = Field(None, description="pH value at this interval")
    viscosity: Optional[str] = Field(None, description="Viscosity value at this interval")

class StabilityTest(BaseModel):
    temp_condition: Optional[str] = Field("80°C", description="Temperature condition for the stability test")
    results: List[StabilityTestRow] = Field(default_factory=list, description="Rows of stability test results")

class OtherTests(BaseModel):
    grains_gel: Optional[str] = Field(None, description="Observation for Grains/Gel")
    wet_strength_n: Optional[str] = Field(None, description="Observation for Wet strength (N)")

class DocumentHeader(BaseModel):
    title: Optional[str] = Field(None, description="Title of the worksheet")
    document_no: Optional[str] = Field(None, description="Document Number")
    revision_no: Optional[str] = Field(None, description="Revision Number")
    effective_date: Optional[str] = Field(None, description="Effective Date")
    next_revision_due: Optional[str] = Field(None, description="Next Revision Due Date")

class PolymerWorksheetSchema(BaseModel):
    # Document Header
    header: Optional[DocumentHeader] = Field(None, description="Standard operating procedure header fields")

    # Batch Details Header
    product_code: Optional[str] = Field(None, description="Product Code")
    ar_no: Optional[str] = Field(None, description="AR. No.")
    batch_no: Optional[str] = Field(None, description="Batch Number")
    containers_packs: Optional[str] = Field(None, description="No. of containers / packs")
    batch_quantity: Optional[str] = Field(None, description="Batch Quantity (e.g., 5900 kg)")
    sampled_quantity: Optional[str] = Field(None, description="Sampled quantity")
    sampling_date: Optional[str] = Field(None, description="Date of sampling / Sampling date")
    analysis_date: Optional[str] = Field(None, description="Date of Analysis")
    release_date: Optional[str] = Field(None, description="Released Date")

    # Main Generic Tests (1 to 8)
    generic_tests: List[WorksheetTestRow] = Field(default_factory=list, description="Standard test rows like Physical Appearance, Viscosity, pH, etc.")

    # Specialized Tests (9, 10, 11)
    solid_content: Optional[SolidContentTest] = Field(None, description="Solid Content (Test 09)")
    stability: Optional[StabilityTest] = Field(None, description="Stability (Test 10)")
    other_tests: Optional[OtherTests] = Field(None, description="Other Tests like Grains/Gel and Wet strength (Test 11)")

    # Footer / Compliance
    compliance_statement: Optional[str] = Field(
        None, description="Logic like 'Product complies to specification'"
    )
    final_remark: Optional[Literal["Approved", "Rejected"]] = Field(None)

    # Signatures
    analyzed_by: Optional[str] = Field(None, description="Name of analyst")
    analyzed_by_date: Optional[str] = Field(None, description="Date of analysis signature")
    checked_by: Optional[str] = Field(None, description="Name of checker")
    checked_by_date: Optional[str] = Field(None, description="Date of checked by signature")
    prepared_by: Optional[str] = Field(None, description="Name of preparer")
    prepared_by_date: Optional[str] = Field(None, description="Date of preparation signature")
    reviewed_by: Optional[str] = Field(None, description="Name of reviewer")
    reviewed_by_date: Optional[str] = Field(None, description="Date of review signature")
    approved_by: Optional[str] = Field(None, description="Name of approver")
    approved_by_date: Optional[str] = Field(None, description="Date of approval signature")

    @validator("generic_tests", each_item=True)
    def normalize_units(cls, v):
        # We can add similar 'CPS' normalization logic here if needed for Worksheet
        return v
