from pydantic import BaseModel, Field
from typing import List, Optional


class TimeCycleRow(BaseModel):
    """A row in the Time Cycle table on BMR Page 1."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    batch_activity: Optional[str] = Field(
        None,
        description="Name of batch activity (e.g., 'RM charging', '7028 addition', 'Batch Maintaining')",
    )
    start_time: Optional[str] = Field(
        None, description="Start time in HH:MM format (e.g., '13:15')"
    )
    end_time: Optional[str] = Field(
        None, description="End time in HH:MM format (e.g., '15:15')"
    )
    total_time: Optional[str] = Field(
        None, description="Total time duration (e.g., '02:00')"
    )
    remarks: Optional[str] = Field(
        None, description="Any remarks for this activity"
    )


class MaterialChargingRow(BaseModel):
    """A row in the Material Charging table on BMR Page 2."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    rm_name: Optional[str] = Field(
        None,
        description="Raw material name/code (e.g., '9063', '7048 - First lot', '7093/ 7053')",
    )
    qty_kgs: Optional[str] = Field(
        None, description="Quantity in Kgs (e.g., '950.29', '91.48')"
    )
    imi_ar_number: Optional[str] = Field(
        None,
        description="I.M.I. / A.R. Number for traceability (e.g., '10012801594', '1108')",
    )
    received_by: Optional[str] = Field(
        None, description="Person who received the material (e.g., 'Anil')"
    )
    checked_by: Optional[str] = Field(
        None, description="Person who checked (e.g., 'Maheesh')"
    )
    remarks: Optional[str] = Field(
        None, description="Additional remarks"
    )


class BatchProcessRow(BaseModel):
    """A row in the Batch Process Record table (BMR Pages 3-8)."""

    sn: Optional[int] = Field(
        None, description="Step/serial number"
    )
    process_detail: Optional[str] = Field(
        None,
        description="Process step description (e.g., '9063 Charging', 'Start stirring', '7028 addition')",
    )
    qty_kgs: Optional[str] = Field(
        None, description="Quantity in Kgs for this step"
    )
    start_time: Optional[str] = Field(
        None, description="Start time"
    )
    end_time: Optional[str] = Field(
        None, description="End time"
    )
    temperature: Optional[str] = Field(
        None, description="Temperature reading (e.g., '24.0', '20.2')"
    )
    remarks: Optional[str] = Field(
        None, description="Operator notes (e.g., 'charge- 9063', 'Chilling Started')"
    )


class BatchReconciliation(BaseModel):
    """Batch reconciliation summary from BMR Page 1."""

    input_kgs: Optional[str] = Field(
        None, description="Input capacity in Kgs (e.g., '6000 kg')"
    )
    output_kgs: Optional[str] = Field(
        None, description="Output capacity in Kgs (e.g., '5900 kg')"
    )
    total_loss_kgs: Optional[str] = Field(
        None, description="Total loss in Kgs (e.g., '100 kg')"
    )
    actual_yield_pct: Optional[str] = Field(
        None, description="Actual yield percentage (e.g., '98.33%')"
    )
    theoretical_yield_pct: Optional[str] = Field(
        None, description="Theoretical yield percentage range (e.g., '98% -100%')"
    )


class PackingMaterialRow(BaseModel):
    """A row in the Packing Material table on BMR Page 1."""

    sn: Optional[int] = Field(
        None, description="Serial number"
    )
    packing: Optional[str] = Field(
        None,
        description="Packing type (e.g., 'Barrels', 'Carboys', 'I.B.C.', 'Others')",
    )
    packing_details: Optional[str] = Field(
        None, description="Packing details"
    )
    total_packing_kgs: Optional[str] = Field(
        None, description="Total packing in Kgs"
    )
    imi_ar_no: Optional[str] = Field(
        None, description="I.M.I. / AR No."
    )
    received_by: Optional[str] = Field(
        None, description="Person who received"
    )


class BMRSchema(BaseModel):
    """Structured data extracted from a Batch Manufacturing Record (typically 8 pages).

    Page 1 = Batch Summary Sheet (reconciliation + time cycle + packing)
    Page 2 = Material Charging + Inhouse Tests
    Pages 3-8 = Batch Process Steps (multi-page table)
    """

    # Header / Identity
    product_name: Optional[str] = Field(
        None, description="Name of product (e.g., '5065')"
    )
    product_rev: Optional[str] = Field(
        None, description="Product revision (e.g., '01')"
    )
    bmr_form_no: Optional[str] = Field(
        None, description="B.M.R. Form number (e.g., 'RR-08-94, REV: 01')"
    )
    batch_number: Optional[str] = Field(
        None, description="Batch number (e.g., '000.10012601674')"
    )
    refer_sop: Optional[str] = Field(
        None, description="Referenced SOP (e.g., 'SOP/5065 REV: 01')"
    )
    effective_date: Optional[str] = Field(
        None, description="BMR Effective Date (DD/MM/YYYY)"
    )
    supersedes: Optional[str] = Field(
        None, description="Supersedes revision (e.g., 'REV: 00')"
    )
    # Shift / Timing
    process_start_shift: Optional[str] = Field(
        None, description="Process start shift (e.g., '3+')"
    )
    process_completion_shift: Optional[str] = Field(
        None, description="Process completion shift (e.g., '2')"
    )
    batch_start_date_time: Optional[str] = Field(
        None, description="Batch start date and time (e.g., '22/01/26')"
    )
    completion_date_time: Optional[str] = Field(
        None, description="Completion date and time (e.g., '23/01/26')"
    )
    total_time_cycle_hrs: Optional[str] = Field(
        None, description="Total time cycle in hours (e.g., '25:45')"
    )
    equipment_tag_no: Optional[str] = Field(
        None, description="Equipment tag number (e.g., 'R-17')"
    )
    # Tables
    batch_reconciliation: Optional[BatchReconciliation] = Field(
        None, description="Batch reconciliation summary"
    )
    time_cycle: List[TimeCycleRow] = Field(
        default_factory=list,
        description="Time cycle activity table",
    )
    packing_material: List[PackingMaterialRow] = Field(
        default_factory=list,
        description="Packing material table",
    )
    material_charging: List[MaterialChargingRow] = Field(
        default_factory=list,
        description="Material charging table from page 2",
    )
    batch_process: List[BatchProcessRow] = Field(
        default_factory=list,
        description="Batch process record rows from pages 3-8",
    )
    # Inhouse Test Results (from Page 2)
    physical_appearance: Optional[str] = Field(
        None, description="Physical appearance (e.g., 'Light yellow color vis. liq.')"
    )
    sp_gravity: Optional[str] = Field(
        None, description="Specific gravity (e.g., '1.060')"
    )
    ph: Optional[str] = Field(
        None, description="pH value (e.g., '3.80')"
    )
    viscosity: Optional[str] = Field(
        None, description="Viscosity (e.g., '80')"
    )
    solid_content: Optional[str] = Field(
        None, description="Solid content (e.g., '17.39')"
    )
    final_output_kgs: Optional[str] = Field(
        None, description="Final output yield in Kgs (e.g., '5900 kg')"
    )
    packing_details: Optional[str] = Field(
        None, description="Packing details notes"
    )
    remarks: Optional[str] = Field(
        None, description="Remarks (e.g., 'Batch Hold in R-alf for mixing')"
    )
    # Signatures
    stirrer_belt_check: Optional[str] = Field(
        None, description="Stirrer belt condition checked by"
    )
    reactor_cleaned_by: Optional[str] = Field(
        None, description="Person who cleaned the reactor"
    )
    reactor_cleaning_checked: Optional[str] = Field(
        None, description="Person who verified reactor cleaning"
    )
    batch_started_executive: Optional[str] = Field(
        None, description="Production Executive who started the batch"
    )
    batch_started_operator: Optional[str] = Field(
        None, description="Operator who started the batch"
    )
    batch_completed_executive: Optional[str] = Field(
        None, description="Production Executive who completed the batch"
    )
    batch_completed_operator: Optional[str] = Field(
        None, description="Operator who completed the batch"
    )
