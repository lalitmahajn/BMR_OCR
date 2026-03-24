from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal


class TestRow(BaseModel):
    """Represents a single row in the physical/chemical parameters test table."""

    sr_no: Optional[int] = Field(
        None, description="The serial number of the test (from the first column)"
    )
    parameter: str = Field(
        description="The name of the physical or chemical test performed (e.g., pH, Viscosity, Physical Appearance, Turbidity, Specific Gravity)"
    )
    result_value: str = Field(
        description="The specific measured numeric or qualitative value resulting from the test"
    )
    unit: Optional[str] = Field(
        None, 
        description="The unit of measurement. NOTE: If parameter is 'Viscosity', ALWAYS return 'CPS'. For Turbidity use 'NTU', for Chloride use 'N'."
    )

    @validator("unit", always=True)
    def force_viscosity_unit(cls, v, values):
        if "parameter" in values and "viscosity" in values["parameter"].lower():
            return "CPS"
        return v


class QCReportSchema(BaseModel):
    """The full structured data extracted from a Finished Goods Q.C. Test Report."""

    product_name: str = Field(
        description="The name of the manufactured product being tested"
    )
    batch_no: str = Field(description="The alphanumeric batch or lot number")
    ar_no: Optional[str] = Field(
        None, description="The AR number (Analytical Report Number) if present"
    )

    mfg_date: Optional[str] = Field(
        None, description="Manufacturing date (typically DD/MM/YYYY or YYYY-MM-DD)"
    )
    exp_date: Optional[str] = Field(
        None, description="Expiry date (typically DD/MM/YYYY or YYYY-MM-DD)"
    )
    approval_date: Optional[str] = Field(
        None, description="The date the batch was approved"
    )

    quantity: Optional[str] = Field(
        None, description="Total quantity of the batch (e.g., '500 KGS', '1000 kg')"
    )
    packing_details: Optional[str] = Field(
        None, description="How the product is packed (e.g., '50 Kg x 10 drums')"
    )

    # Table Extraction
    test_results: List[TestRow] = Field(
        description="The main table listing all physical and chemical parameters tested and their results."
    )

    # Footer Extraction & Legal Compliance
    overall_result: Optional[Literal["APPROVED", "REJECTED"]] = Field(
        None, 
        description="The final decision. NOTE: Look for tick marks or cross-outs on the paper to determine if the batch was APPROVED or REJECTED."
    )
    remarks: Optional[str] = Field(
        None,
        description="Any additional remarks or notes left at the bottom of the document",
    )

    analyzed_date: Optional[str] = Field(
        None,
        description="The date the document was analyzed (from the Analyzed By section)",
    )
    approved_date: Optional[str] = Field(
        None,
        description="The date the document was approved (from the Approved By section)",
    )

    analyzed_by_role: str = Field(
        "QC Executive", description="The role of the person who analyzed the sample"
    )
    approved_by_role: str = Field(
        "QC Manager / Incharge", description="The role of the person who approved the sample"
    )

    analyzed_by_signature_present: Optional[bool] = Field(
        False,
        description="True if there is a written signature or initials in the 'Analyzed By' section",
    )
    approved_by_signature_present: Optional[bool] = Field(
        False,
        description="True if there is a written signature or initials in the 'Approved By' section",
    )
