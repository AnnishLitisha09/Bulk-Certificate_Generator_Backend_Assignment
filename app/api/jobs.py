"""
API routes for bulk generation job creation, tracking, and queries.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CreateJobRequest,
    JobResponse,
    PaginatedRecipientsResponse,
)
from app.services.job_service import (
    create_and_process_job,
    format_job_response,
    format_recipient_response,
    generate_job_certificates_zip,
    get_job_by_id,
    get_job_recipients,
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bulk certificate generation job",
    description=(
        "Accepts bulk certificate parameters and a list of recipients. "
        "Validates input, processes each recipient independently, renders PDF certificates, "
        "and returns job summary with individual recipient results."
    ),
)
def create_job(
    request: CreateJobRequest,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Create and execute a bulk certificate generation job."""
    job = create_and_process_job(db=db, request_data=request)
    return format_job_response(job, include_recipients=True)


@router.get(
    "/{job_id}/",
    response_model=JobResponse,
    summary="Get job status and progress",
    description="Retrieve detailed status, counts, progress percentage, and timestamps for a job.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Retrieve job details by job_id."""
    job = get_job_by_id(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job with ID '{job_id}' not found",
        )
    return format_job_response(job, include_recipients=True)


@router.get(
    "/{job_id}/recipients/",
    response_model=PaginatedRecipientsResponse,
    summary="List recipients and results for a job",
    description="Retrieve paginated recipient outcomes and certificate download links for a specific job.",
)
def list_job_recipients(
    job_id: str,
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status: SUCCESS, FAILED, or PENDING"
    ),
    db: Session = Depends(get_db),
) -> PaginatedRecipientsResponse:
    """List paginated recipients for a job."""
    job = get_job_by_id(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job with ID '{job_id}' not found",
        )

    total, recipients = get_job_recipients(
        db=db,
        job_id=job_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    items = [format_recipient_response(r) for r in recipients]

    return PaginatedRecipientsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/{job_id}/download/",
    summary="Download all generated certificates as a ZIP archive",
    description="Streams a compressed ZIP file containing every successfully generated PDF certificate for this job.",
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Returns ZIP archive containing all certificates.",
        },
        404: {
            "description": "Job not found.",
        },
        400: {
            "description": "No generated certificates available for this job.",
        },
    },
)
def download_all_job_certificates(
    job_id: str,
    db: Session = Depends(get_db),
) -> Response:
    """Download all generated certificates for a job as a single ZIP archive."""
    try:
        zip_bytes, zip_filename = generate_job_certificates_zip(db=db, job_id=job_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
        },
    )

