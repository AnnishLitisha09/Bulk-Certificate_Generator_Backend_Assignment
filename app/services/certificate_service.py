"""
Service handling certificate generation, file storage, security checks, and retrieval.
"""

import logging
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Certificate, GenerationJob, Recipient, RecipientStatus, utc_now
from app.utils.pdf_generator import generate_certificate_pdf

logger = logging.getLogger(__name__)
settings = get_settings()


def sanitize_filename(name: str) -> str:
    """
    Sanitize recipient or event string to be safe for filenames.
    Strips non-alphanumeric characters except underscores and dashes.
    """
    clean = re.sub(r"[^\w\s-]", "", name).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    return clean or "recipient"


def validate_recipient_data(name: str, email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate individual recipient data.
    Enforces non-empty name and RFC-compliant email structure.

    Returns:
        (is_valid, error_message)
    """
    name_clean = name.strip() if name else ""
    if not name_clean:
        return False, "Recipient name cannot be empty or whitespace"
    if len(name_clean) > 255:
        return False, "Recipient name exceeds maximum allowed length of 255 characters"

    email_clean = email.strip() if email else ""
    if not email_clean:
        return False, "Recipient email cannot be empty"

    try:
        # Validate email syntax without external DNS checks for speed & determinism
        validate_email(email_clean, check_deliverability=False)
    except EmailNotValidError as exc:
        return False, f"Invalid email format: {str(exc)}"

    return True, None


def generate_and_save_certificate(
    db: Session,
    job: GenerationJob,
    recipient: Recipient,
) -> Certificate:
    """
    Generate PDF certificate file, persist Certificate record, and update Recipient.

    Args:
        db: Database session.
        job: Parent GenerationJob.
        recipient: Recipient model instance.

    Returns:
        Certificate: Created Certificate entity.
    """
    certificate_id = str(uuid.uuid4())
    safe_recipient_name = sanitize_filename(recipient.name)
    download_filename = f"certificate_{safe_recipient_name}_{certificate_id[:8]}.pdf"

    # Save to storage directory with UUID filename for security and uniqueness
    storage_root = settings.storage_path
    pdf_dest_path = (storage_root / f"{certificate_id}.pdf").resolve()

    # Relative path stored in database
    relative_path = f"{settings.STORAGE_DIR}/{certificate_id}.pdf"

    # Generate PDF through dedicated ReportLab utility
    generate_certificate_pdf(
        output_path=pdf_dest_path,
        certificate_id=certificate_id,
        recipient_name=recipient.name,
        event_name=job.event_name,
        organization_name=job.organization_name,
        certificate_title=job.certificate_title,
        issue_date=job.issue_date,
        certificate_text=recipient.certificate_text,
    )

    # Create certificate record
    certificate = Certificate(
        id=certificate_id,
        recipient_id=recipient.id,
        job_id=job.id,
        file_path=relative_path,
        filename=download_filename,
        created_at=utc_now(),
    )
    db.add(certificate)

    # Update recipient record
    recipient.certificate_id = certificate_id
    recipient.status = RecipientStatus.SUCCESS.value
    recipient.error_message = None
    recipient.completed_at = utc_now()

    db.flush()
    return certificate


def get_certificate_file_path(
    db: Session,
    certificate_id: str,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Retrieve and validate the physical file path for a certificate ID.
    Guarantees path traversal protection by ensuring the target file
    is strictly within the configured storage directory.

    Returns:
        (Path to file, download filename) or (None, None) if not found or invalid.
    """
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        return None, None

    storage_root = settings.storage_path
    # Physical file is named {certificate_id}.pdf inside storage_root
    expected_path = (storage_root / f"{certificate_id}.pdf").resolve()

    # Path traversal check
    try:
        expected_path.relative_to(storage_root)
    except ValueError:
        logger.warning(
            "Path traversal attempt or mismatch detected for certificate %s", certificate_id
        )
        return None, None

    if not expected_path.exists() or not expected_path.is_file():
        logger.error(
            "Certificate file missing on disk for certificate %s at %s",
            certificate_id,
            expected_path,
        )
        return None, None

    return expected_path, cert.filename
