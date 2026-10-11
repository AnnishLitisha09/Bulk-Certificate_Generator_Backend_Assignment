"""
Core business logic service for creating, processing, and querying bulk certificate jobs.
Keeps route handlers thin and decouples processing logic from HTTP requests.
"""

import io
import logging
import uuid
import zipfile
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    Certificate,
    GenerationJob,
    JobStatus,
    Recipient,
    RecipientStatus,
    utc_now,
)
from app.schemas import (
    CreateJobRequest,
    JobResponse,
    RecipientDetailResponse,
)
from app.services.certificate_service import (
    generate_and_save_certificate,
    get_certificate_file_path,
    sanitize_filename,
    validate_recipient_data,
)

logger = logging.getLogger(__name__)


def create_and_process_job(db: Session, request_data: CreateJobRequest) -> GenerationJob:
    """
    Synchronously orchestrates a bulk certificate generation job.
    1. Creates and persists the GenerationJob record in PROCESSING status.
    2. Persists Recipient records for all items in the request.
    3. Iterates through each recipient independently:
       - Validates recipient-level fields (name, email format).
       - Generates and persists PDF certificate for valid recipients within savepoints.
       - Isolates errors so that individual failures do NOT halt remaining recipients.
    4. Updates final job counts, status, and completion timestamp.

    Args:
        db: Active database session.
        request_data: Validated bulk generation request schema.

    Returns:
        GenerationJob: The finished job instance with all recipient records attached.
    """
    job_id = str(uuid.uuid4())
    total_recipients = len(request_data.recipients)

    # 1. Create Job record
    job = GenerationJob(
        id=job_id,
        event_name=request_data.event_name,
        organization_name=request_data.organization_name,
        certificate_title=request_data.certificate_title,
        issue_date=request_data.issue_date,
        status=JobStatus.PROCESSING.value,
        total_recipients=total_recipients,
        successful_count=0,
        failed_count=0,
        created_at=utc_now(),
    )
    db.add(job)

    # 2. Create initial Recipient records
    recipient_instances: List[Recipient] = []
    for item in request_data.recipients:
        rec_instance = Recipient(
            id=str(uuid.uuid4()),
            job_id=job_id,
            name=item.name,
            email=item.email,
            certificate_text=item.certificate_text,
            status=RecipientStatus.PENDING.value,
            created_at=utc_now(),
        )
        db.add(rec_instance)
        recipient_instances.append(rec_instance)

    # Persist job and recipient baseline before processing starts
    db.commit()
    db.refresh(job)

    successful_count = 0
    failed_count = 0

    # 3. Process each recipient independently
    for recipient in recipient_instances:
        rec_id = recipient.id

        # Step 3a: Recipient-level data validation
        is_valid, validation_error = validate_recipient_data(
            name=recipient.name,
            email=recipient.email,
        )

        if not is_valid:
            logger.info("Recipient %s failed validation: %s", rec_id, validation_error)
            recipient.status = RecipientStatus.FAILED.value
            recipient.error_message = validation_error
            recipient.completed_at = utc_now()
            failed_count += 1
            db.commit()
            continue

        # Step 3b: Certificate generation attempt using database SAVEPOINT
        try:
            # Use begin_nested() so individual failure rolls back only this recipient
            with db.begin_nested():
                generate_and_save_certificate(db=db, job=job, recipient=recipient)
            successful_count += 1
            db.commit()
        except Exception as exc:
            logger.exception(
                "Failed to generate certificate for recipient %s: %s",
                rec_id,
                exc,
            )
            # Re-fetch recipient in session to update failure status
            rec = db.query(Recipient).filter(Recipient.id == rec_id).first()
            if rec:
                rec.status = RecipientStatus.FAILED.value
                rec.error_message = f"Generation error: {str(exc)}"
                rec.completed_at = utc_now()
                db.commit()
            failed_count += 1

    # 4. Finalize Job Status
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    job.successful_count = successful_count
    job.failed_count = failed_count
    job.completed_at = utc_now()

    if successful_count == total_recipients:
        job.status = JobStatus.COMPLETED.value
    elif successful_count > 0 and failed_count > 0:
        job.status = JobStatus.COMPLETED_WITH_ERRORS.value
    else:
        # All recipients failed
        job.status = JobStatus.FAILED.value

    db.commit()
    db.refresh(job)

    return job


def get_job_by_id(db: Session, job_id: str) -> Optional[GenerationJob]:
    """Retrieve a GenerationJob by ID."""
    return db.query(GenerationJob).filter(GenerationJob.id == job_id).first()


def get_job_recipients(
    db: Session,
    job_id: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
) -> Tuple[int, List[Recipient]]:
    """
    Retrieve paginated recipients for a specific job with optional status filtering.

    Returns:
        (total_count, list_of_recipients)
    """
    query = db.query(Recipient).filter(Recipient.job_id == job_id)

    if status:
        query = query.filter(Recipient.status == status.upper())

    total = query.count()
    offset = (page - 1) * page_size
    recipients = (
        query.order_by(Recipient.created_at)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return total, recipients


def format_recipient_response(recipient: Recipient) -> RecipientDetailResponse:
    """Format a Recipient database model into RecipientDetailResponse."""
    download_url = None
    if recipient.certificate_id and recipient.status == RecipientStatus.SUCCESS.value:
        download_url = f"/api/certificates/{recipient.certificate_id}/"

    return RecipientDetailResponse(
        id=recipient.id,
        job_id=recipient.job_id,
        name=recipient.name,
        email=recipient.email,
        certificate_text=recipient.certificate_text,
        status=recipient.status,
        error_message=recipient.error_message,
        certificate_id=recipient.certificate_id,
        download_url=download_url,
        created_at=recipient.created_at,
        completed_at=recipient.completed_at,
    )


def format_job_response(
    job: GenerationJob,
    include_recipients: bool = True,
) -> JobResponse:
    """Format a GenerationJob database model into a JobResponse schema."""
    pending_count = max(0, job.total_recipients - job.successful_count - job.failed_count)

    if job.total_recipients > 0:
        processed = job.successful_count + job.failed_count
        progress_percentage = round((processed / job.total_recipients) * 100.0, 2)
    else:
        progress_percentage = 100.0

    recipients_data = None
    if include_recipients and job.recipients:
        recipients_data = [format_recipient_response(r) for r in job.recipients]

    return JobResponse(
        id=job.id,
        event_name=job.event_name,
        organization_name=job.organization_name,
        certificate_title=job.certificate_title,
        issue_date=job.issue_date,
        status=job.status,
        total_recipients=job.total_recipients,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        pending_count=pending_count,
        progress_percentage=progress_percentage,
        created_at=job.created_at,
        completed_at=job.completed_at,
        recipients=recipients_data,
    )


def generate_job_certificates_zip(db: Session, job_id: str) -> Tuple[bytes, str]:
    """
    Generate an in-memory ZIP archive of all successfully generated certificates for a job.
    Returns:
        (zip_bytes, zip_filename)
    Raises:
        LookupError: If job does not exist.
        ValueError: If job has no successfully generated certificates.
    """
    job = get_job_by_id(db=db, job_id=job_id)
    if not job:
        raise LookupError(f"Generation job with ID '{job_id}' not found")

    certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    if not certificates:
        raise ValueError(f"No generated certificates available for job '{job_id}'")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for cert in certificates:
            file_path, filename = get_certificate_file_path(db=db, certificate_id=cert.id)
            if file_path and file_path.exists():
                zf.write(file_path, arcname=filename or cert.filename)

    buffer.seek(0)
    safe_event = sanitize_filename(job.event_name)
    zip_filename = f"certificates_{safe_event}_{job_id[:8]}.zip"
    return buffer.getvalue(), zip_filename

