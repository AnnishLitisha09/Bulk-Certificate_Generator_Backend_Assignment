"""
SQLAlchemy models representing jobs, recipients, and certificates.
"""

from datetime import datetime, timezone
import enum
import uuid
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class JobStatus(str, enum.Enum):
    """Lifecycle statuses for a bulk generation job."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class RecipientStatus(str, enum.Enum):
    """Status for an individual recipient generation attempt."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class GenerationJob(Base):
    """
    Represents a bulk certificate generation job.
    Tracks batch metadata, execution progress, and outcome counts.
    """
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_title: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default=JobStatus.PENDING.value, index=True, nullable=False
    )
    total_recipients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    recipients: Mapped[List["Recipient"]] = relationship(
        "Recipient",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Recipient.created_at",
    )
    certificates: Mapped[List["Certificate"]] = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_generation_jobs_status_created", "status", "created_at"),
    )


class Recipient(Base):
    """
    Represents a recipient in a bulk generation job.
    Records recipient data, outcome status, error messages, and reference to certificate.
    """
    __tablename__ = "recipients"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=RecipientStatus.PENDING.value, index=True, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    job: Mapped["GenerationJob"] = relationship("GenerationJob", back_populates="recipients")
    certificate: Mapped[Optional["Certificate"]] = relationship(
        "Certificate",
        back_populates="recipient",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Certificate(Base):
    """
    Represents a successfully generated PDF certificate document.
    Stores metadata and secure relative file path.
    """
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("recipients.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    job: Mapped["GenerationJob"] = relationship("GenerationJob", back_populates="certificates")
    recipient: Mapped["Recipient"] = relationship("Recipient", back_populates="certificate")
