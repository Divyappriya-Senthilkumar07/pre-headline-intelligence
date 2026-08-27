import os
import shutil
import logging
from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.extractors.audio_extractor import AudioExtractor

logger = logging.getLogger(__name__)


class VideoExtractor(BaseExtractor):
    """
    Video Ingestion Foundation.
    Pipeline stages:
    1. Audio track separation
    2. Audio transcription (via AudioExtractor)
    3. Keyframe sampling
    4. Frame OCR extraction
    5. Aggregate synthesis into MediaExtraction
    """

    def __init__(self):
        self.audio_extractor = AudioExtractor()

    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        if not os.path.exists(file_path):
            return ExtractionResult(
                extraction_method="VIDEO_PIPELINE",
                success=False,
                error_message=f"Video file not found: {file_path}",
                is_meaningful=False,
            )

        ffmpeg_cmd = shutil.which("ffmpeg")
        metadata = {
            "mime_type": mime_type,
            "filename": original_filename,
            "ffmpeg_available": ffmpeg_cmd is not None,
        }

        if not ffmpeg_cmd:
            # Clean diagnostic failure per spec
            return ExtractionResult(
                extracted_text="",
                extraction_method="VIDEO_FFMPEG_UNAVAILABLE",
                confidence=0.0,
                detected_language="unknown",
                extracted_metadata=metadata,
                is_meaningful=False,
                success=False,
                error_message=(
                    "FFmpeg binary not detected on system PATH. "
                    "Install ffmpeg to enable automated video track separation and keyframe OCR sampling."
                ),
            )

        # If ffmpeg is available, execute separation pipeline
        # (In Phase 1, placeholder audio separation step)
        return ExtractionResult(
            extracted_text="Video ingestion pipeline initialized.",
            extraction_method="VIDEO_PIPELINE_STUB",
            confidence=0.5,
            detected_language="en",
            extracted_metadata=metadata,
            is_meaningful=False,
            success=True,
        )
