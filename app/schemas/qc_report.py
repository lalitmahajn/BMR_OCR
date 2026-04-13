from pydantic import BaseModel, Field
from typing import Optional, Literal


class Page1Tests(BaseModel):
    """The handwritten measured values for the 14 pre-printed test parameters.
    Extract ONLY the value/result for each parameter. Do not include units like CPS or NTU unless they are scribbled.
    """
    physical_appearance: str = Field(description="Result for 'Physical Appearance'")
    viscosity: str = Field(description="Result for 'Viscosity'")
    ph: str = Field(description="Result for 'pH'")
    specific_gravity: str = Field(description="Result for 'Specific Gravity @ 25°C'")
    solid_content: str = Field(description="Result for 'Solid Content / Active %'")
    ionicity: str = Field(description="Result for 'Ionicity'")
    charge: str = Field(description="Result for 'Charge'")
    solubility: str = Field(description="Result for 'Solubility'")
    turbidity: str = Field(description="Result for 'Turbidity'")
    color_gardner: str = Field(description="Result for 'Color Gardner'")
    presence_of_grains: str = Field(description="Result for 'Presence of Grains / Gel'")
    stability_test: str = Field(description="Result for 'Stability Test / Boring Test'")
    performance_test: str = Field(description="Result for 'Performance Test / Cobb Value'")
    tensile_strength: str = Field(description="Result for 'Tensile Strength Test / Chloride Content'")


class QCReportSchema(BaseModel):
    """Finished Good Q.C. Test Report for Speciality Chemicals.
    Single-page document with 8 header fields, 14 explicit test results, and footer fields.
    """

    # Header fields (in document layout order)
    product_name: str = Field(
        description="Product name (e.g., 'RL-5065')"
    )
    mfg_date: str = Field(
        description="Manufacturing date (DD/MM/YYYY) (e.g., '23/01/2026')"
    )
    ar_no: str = Field(
        description="AR number in format like 'R/26/FG/01674'"
    )
    approval_date: str = Field(
        description="Approval date (DD/MM/YYYY) (e.g., '28/01/2026')"
    )
    batch_no: str = Field(
        description="Batch number (e.g., '100/260/674')"
    )
    packing_details: str = Field(
        description="Packing details (e.g., '5900 Kg x 01')"
    )
    quantity: str = Field(
        description="Quantity value only, no unit (e.g., '5900')"
    )
    exp_date: str = Field(
        description="Expiry date (DD/MM/YYYY) (e.g., '22/07/2026')"
    )

    # Test Results (Explicit Fields)
    page_1_tests: Page1Tests = Field(
        description="The handwritten test results for the 14 standard parameters."
    )

    # Footer fields
    result: Literal["APPROVED", "REJECTED"] = Field(
        description="Final result — either 'APPROVED' or 'REJECTED'. Look for strikethrough or tick mark."
    )
    remarks: Optional[str] = Field(
        None,
        description="Remarks text at the bottom (e.g., 'U1D High Viscosity')"
    )
