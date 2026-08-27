from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    """Normalized output contract returned by all media extractors."""
    extracted_text: str = ""
    extraction_method: str = Field(..., description="Method used (DIRECT_TEXT, OCR_TESSERACT, AUDIO_STT, etc.)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    detected_language: str = "unknown"
    language_confidence: float = 0.0
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_meaningful: bool = Field(default=True, description="True if extracted text has actionable content for Article normalization")
    success: bool = True
    error_message: Optional[str] = None
    extraction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseExtractor(ABC):
    """Abstract base class for all file and media content extractors."""

    @abstractmethod
    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        """Extract textual content and metadata from media file."""
        pass
