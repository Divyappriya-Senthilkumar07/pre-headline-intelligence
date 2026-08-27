import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now


class MediaTypeEnum(str, enum.Enum):
    IMAGE = "IMAGE"
    PDF = "PDF"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    TEXT = "TEXT"


class MediaProcessingStatusEnum(str, enum.Enum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Media(Base, TimestampMixin):
    """
    Analyst-provided media entity foundation for multi-modal intelligence ingestion.
    Supports Image, PDF, Audio, Video, and raw text document files.
    """
    __tablename__ = "media"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Processing state
    processing_status: Mapped[str] = mapped_column(String(50), default=MediaProcessingStatusEnum.UPLOADED.value, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    jobs: Mapped[List["MediaProcessingJob"]] = relationship("MediaProcessingJob", back_populates="media", cascade="all, delete-orphan")
    extractions: Mapped[List["MediaExtraction"]] = relationship("MediaExtraction", back_populates="media", cascade="all, delete-orphan")


class MediaProcessingJob(Base, TimestampMixin):
    """
    Tracking record for background processing jobs associated with uploaded media.
    """
    __tablename__ = "media_processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_id: Mapped[str] = mapped_column(String(36), ForeignKey("media.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)  # OCR, TRANSCRIPTION, ENTITY_EXTRACTION, FRAME_ANALYSIS
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    media: Mapped["Media"] = relationship("Media", back_populates="jobs")


class MediaExtraction(Base, TimestampMixin):
    """
    Structured extractions resulting from media processing (text transcripts, OCR blocks, entities).
    """
    __tablename__ = "media_extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_id: Mapped[str] = mapped_column(String(36), ForeignKey("media.id", ondelete="CASCADE"), nullable=False, index=True)
    extraction_type: Mapped[str] = mapped_column(String(100), nullable=False)  # OCR_TEXT, AUDIO_TRANSCRIPT, DOCUMENT_STRUCTURE
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_entities: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(default=1.0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    media: Mapped["Media"] = relationship("Media", back_populates="extractions")
