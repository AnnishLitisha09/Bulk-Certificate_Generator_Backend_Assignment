"""
API routes for certificate retrieval and PDF downloads.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.certificate_service import get_certificate_file_path

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}/",
    response_class=FileResponse,
    summary="Download generated PDF certificate",
    description=(
        "Stream the generated PDF certificate document. "
        "Validates certificate existence and verifies file boundaries to prevent directory traversal."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the generated PDF certificate.",
        },
        404: {
            "description": "Certificate or associated PDF file not found.",
        },
    },
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download a successfully generated PDF certificate by ID."""
    file_path, filename = get_certificate_file_path(
        db=db, certificate_id=certificate_id
    )

    if not file_path or not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' was not found or file is unavailable",
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
        content_disposition_type="inline",
    )
