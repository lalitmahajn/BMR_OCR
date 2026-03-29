from pydantic import BaseModel, Field
from typing import List, Optional


class EmailDataRow(BaseModel):
    """A single row in the optional data table embedded in an email."""

    sr_no: Optional[int] = Field(
        None, description="Serial number"
    )
    sample_name: Optional[str] = Field(
        None, description="Product or sample name (e.g., '5065')"
    )
    batch_no: Optional[str] = Field(
        None, description="Batch number (e.g., '10012601674')"
    )
    dose: Optional[str] = Field(
        None, description="Dosage used in test (e.g., '6Kg/T')"
    )
    gsm: Optional[str] = Field(
        None, description="GSM value (e.g., '61.57')"
    )
    strength_newton: Optional[str] = Field(
        None, description="Strength measurement in Newton (e.g., '7.21 N')"
    )
    wet_strength_ratio: Optional[str] = Field(
        None, description="Wet strength ratio percentage (e.g., '25.31')"
    )


class EmailSchema(BaseModel):
    """Structured data extracted from an email attachment (Gmail print)."""

    subject: Optional[str] = Field(
        None,
        description="Email subject line (e.g., 'Wet & % Wet Strength Of 5065')",
    )
    from_email: Optional[str] = Field(
        None,
        description="Sender email address and name (e.g., 'Research Development <rd@rmc.in>')",
    )
    to_email: Optional[str] = Field(
        None,
        description="Recipient email addresses",
    )
    cc_email: Optional[str] = Field(
        None,
        description="CC email addresses if present",
    )
    date_sent: Optional[str] = Field(
        None,
        description="Date and time the email was sent (e.g., 'Sat, Jan 24, 2026 at 2:22 PM')",
    )
    message_count: Optional[str] = Field(
        None, description="Number of messages in the thread (e.g., '1 message')"
    )
    data_table: List[EmailDataRow] = Field(
        default_factory=list,
        description="Optional data table embedded in the email body with test results",
    )
    signature_name: Optional[str] = Field(
        None,
        description="Sender's sign-off name or 'Thanks & Regards' section",
    )
    department: Optional[str] = Field(
        None,
        description="Sender's department (e.g., 'R & D Dept.')",
    )
    company: Optional[str] = Field(
        None,
        description="Company name from the signature block",
    )
