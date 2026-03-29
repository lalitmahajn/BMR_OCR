from pydantic import BaseModel, Field
from typing import List, Optional


class DeviationTestRow(BaseModel):
    """A single row in the deviation test results table."""

    parameter: str = Field(
        description="Name of the test parameter (e.g., 'Viscosity')"
    )
    std_specification: Optional[str] = Field(
        None, description="Standard specification range (e.g., '20 TO 80')"
    )
    inhouse_specification: Optional[str] = Field(
        None, description="In-house RM specification range (e.g., '30 TO 70')"
    )
    test_result: Optional[str] = Field(
        None, description="Actual test result with unit (e.g., '78 CPS')"
    )
    remarks: Optional[str] = Field(
        None,
        description="Compliance remarks (e.g., 'complies with std specs but not complies with in-house spec')",
    )


class DeviationAcceptanceSchema(BaseModel):
    """Structured data extracted from an Acceptance Under Deviation form."""

    material_name: Optional[str] = Field(
        None,
        description="Name of RM/FP/PM material (e.g., 'RL-5065')",
    )
    supplier_lot_batch_no: Optional[str] = Field(
        None,
        description="Supplier Lot No. / Batch No (e.g., '10010601674')",
    )
    quantity: Optional[str] = Field(
        None, description="Quantity with unit (e.g., '5900 kg')"
    )
    imi_ar_no: Optional[str] = Field(
        None,
        description="IMI / A.R. Number for traceability (e.g., 'R1061FG101674')",
    )
    vendor_name: Optional[str] = Field(
        None, description="Vendor or Supplier name (e.g., 'RMCPL')"
    )
    date_of_testing: Optional[str] = Field(
        None, description="Date of testing (DD/MM/YY format)"
    )
    test_results: List[DeviationTestRow] = Field(
        default_factory=list,
        description="Table of test parameters with specifications and results",
    )
    # Approval signatures
    qcm_signature_date: Optional[str] = Field(
        None, description="Date of QCM approval"
    )
    qam_signature_date: Optional[str] = Field(
        None, description="Date of QAM pre-approval"
    )
    ed_signature_date: Optional[str] = Field(
        None, description="Date of ED approval"
    )
    form_no: Optional[str] = Field(
        None, description="Form number (e.g., 'RR-14-04, Rev: 00')"
    )
