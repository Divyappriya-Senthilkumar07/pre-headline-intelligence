from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.media import MediaTypeEnum, MediaProcessingStatusEnum


class MediaBase(BaseModel):
    original_filename: str
    mime_type: str
    media_type: str
    file_size_bytes: int
    source_metadata: Dict[str, Any] = Field(default_factory=dict)


class MediaCreate(MediaBase):
    storage_reference: str


class ExtractionItemRead(BaseModel):
    id: str
    extraction_type: str
    extracted_text: Optional[str] = None
    confidence_score: float
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaRead(MediaBase):
    id: str
    upload_timestamp: datetime
    processing_status: str
    processing_error: Optional[str] = None
    storage_reference: str
    created_at: datetime
    updated_at: datetime
    extractions: List[ExtractionItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MediaStatusResponse(BaseModel):
    media_id: str
    filename: str
    media_type: str
    status: str
    progress_percent: int = 100
    current_step: str = "COMPLETED"
    error_message: Optional[str] = None
    created_at: datetime
    is_completed: bool = False
    is_failed: bool = False


class MediaUploadResponse(BaseModel):
    """
    Spec-compliant upload response containing required fields:
    id, filename, media_type, MIME type, size, processing_status, created_at
    """
    id: str
    filename: str
    media_type: str
    mime_type: str
    size: int
    processing_status: str
    created_at: datetime
    message: str = "Media uploaded and queued for extraction."


class MediaProcessingJobRead(BaseModel):
    id: str
    media_id: str
    job_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaDeleteResponse(BaseModel):
    media_id: str
    success: bool
    message: str


class MediaRetryResponse(BaseModel):
    media_id: str
    status: str
    message: str
