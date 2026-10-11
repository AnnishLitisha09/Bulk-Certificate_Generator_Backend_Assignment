"""
Pydantic schemas for request validation, response serialization, and data transfer.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RecipientInput(BaseModel):
    """
    Input schema for an individual recipient in a bulk request.
    Fields are kept permissive at the HTTP boundary so that recipient-level errors
    (e.g., malformed email or empty name) can be captured independently per recipient
    rather than rejecting the entire batch of valid recipients.
    """
    name: str = Field(..., max_length=255, description="Full name of recipient")
    email: str = Field(..., max_length=255, description="Recipient email address")
    certificate_text: Optional[str] = Field(
        None, max_length=1000, description="Custom certificate text"
    )

    @field_validator("name", "email", mode="before")
    @classmethod
    def convert_to_string(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("certificate_text", mode="before")
    @classmethod
    def clean_text(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


class CreateJobRequest(BaseModel):
    """
    Request-level schema for creating a bulk certificate generation job.
    Enforces required fields, string lengths, and reasonable batch size limits.
    """
    event_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the event or course"
    )
    organization_name: str = Field(
        ..., min_length=1, max_length=255, description="Issuing organization"
    )
    certificate_title: str = Field(
        ..., min_length=1, max_length=255, description="Title printed on the certificate"
    )
    issue_date: str = Field(
        ..., min_length=1, max_length=50, description="Date formatted string (e.g. YYYY-MM-DD)"
    )
    recipients: List[RecipientInput] = Field(
        ..., min_length=1, max_length=500, description="List of recipients (1 to 500 items)"
    )

    @field_validator("event_name", "organization_name", "certificate_title", "issue_date")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError(f"'{info.field_name}' cannot be empty or blank")
        return v_stripped

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_name": "Python Programming Workshop",
                "organization_name": "ABC College",
                "certificate_title": "Certificate of Participation",
                "issue_date": "2026-10-11",
                "recipients": [
                    {
                        "name": "Annish Litisha",
                        "email": "litisha@example.com",
                        "certificate_text": "For successfully participating in the workshop."
                    },
                    {
                        "name": "Liti",
                        "email": "liti@example.com",
                        "certificate_text": "For successfully completing the workshop."
                    }
                ]
            }
        }
    }


class RecipientDetailResponse(BaseModel):
    """Detailed response for an individual recipient."""
    id: str
    job_id: str
    name: str
    email: str
    certificate_text: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    certificate_id: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    """
    Response model for job creation and status endpoints.
    Provides batch metadata, counts, progress percentage, and recipient outcomes.
    """
    id: str
    event_name: str
    organization_name: str
    certificate_title: str
    issue_date: str
    status: str
    total_recipients: int
    successful_count: int
    failed_count: int
    pending_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    recipients: Optional[List[RecipientDetailResponse]] = None

    model_config = {"from_attributes": True}


class PaginatedRecipientsResponse(BaseModel):
    """Paginated list of recipients for a job."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[RecipientDetailResponse]


class HealthResponse(BaseModel):
    """System health check response."""
    status: str
    app_name: str
    version: str
    timestamp: datetime
