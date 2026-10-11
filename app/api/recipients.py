"""
API routes for querying individual recipient records.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recipient
from app.schemas import RecipientDetailResponse
from app.services.job_service import format_recipient_response

router = APIRouter(prefix="/api/recipients", tags=["Recipients"])


@router.get(
    "/{recipient_id}/",
    response_model=RecipientDetailResponse,
    summary="Get individual recipient details",
    description="Retrieve generation status, failure reason, and certificate link for an individual recipient.",
)
def get_recipient(
    recipient_id: str,
    db: Session = Depends(get_db),
) -> RecipientDetailResponse:
    """Retrieve an individual recipient record."""
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID '{recipient_id}' not found",
        )
    return format_recipient_response(recipient)
