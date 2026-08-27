import os
import wave
import logging
from typing import Optional
from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class AudioTranscriptionProvider:
    """
    Pluggable Audio Transcription Provider interface.
    Can be backed by local Faster-Whisper, OpenAI Whisper API, or Google Cloud Speech.
    """

    async def transcribe(self, file_path: str) -> Optional[str]:
        # Production STT engine hook
        return None


class AudioExtractor(BaseExtractor):
    """
    Audio Ingestion and Speech-To-Text Foundation.
    Validates audio file integrity, reads audio duration/channels,
    and dispatches to configured STT provider.
    NOTE: In accordance with project requirements, if no STT model or provider is configured,
    the job cleanly surfaces a meaningful failure instead of faking results.
    """

    def __init__(self, provider: Optional[AudioTranscriptionProvider] = None):
        self.provider = provider or AudioTranscriptionProvider()

    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        if not os.path.exists(file_path):
            return ExtractionResult(
                extraction_method="AUDIO_STT",
                success=False,
                error_message=f"Audio file not found: {file_path}",
                is_meaningful=False,
            )

        # Inspect basic audio container info if WAV
        audio_metadata = {
            "mime_type": mime_type,
            "filename": original_filename,
        }

        try:
            if file_path.lower().endswith(".wav"):
                try:
                    with wave.open(file_path, "rb") as wf:
                        channels = wf.getnchannels()
                        framerate = wf.getframerate()
                        nframes = wf.getnframes()
                        duration_sec = round(nframes / float(framerate), 2)
                        audio_metadata.update({
                            "channels": channels,
                            "framerate": framerate,
                            "duration_seconds": duration_sec,
                        })
                except Exception:
                    pass

            # Attempt STT via provider
            transcript = await self.provider.transcribe(file_path)

            if transcript and transcript.strip():
                lang, lang_conf = LanguageService.detect_language(transcript)
                return ExtractionResult(
                    extracted_text=transcript.strip(),
                    extraction_method="AUDIO_STT_PROVIDER",
                    confidence=0.88,
                    detected_language=lang,
                    language_confidence=lang_conf,
                    extracted_metadata=audio_metadata,
                    is_meaningful=True,
                    success=True,
                )
            else:
                # Surfaced failure per spec: "If transcription cannot be performed, the processing job must become FAILED with a meaningful error"
                return ExtractionResult(
                    extracted_text="",
                    extraction_method="AUDIO_STT_UNAVAILABLE",
                    confidence=0.0,
                    detected_language="unknown",
                    extracted_metadata=audio_metadata,
                    is_meaningful=False,
                    success=False,
                    error_message=(
                        "Local STT engine (Faster-Whisper / Whisper) is not active in this development environment. "
                        "Configure LLM/STT provider in .env to enable automated speech transcription."
                    ),
                )

        except Exception as e:
            logger.error(f"Audio processing failed for {original_filename}: {e}", exc_info=True)
            return ExtractionResult(
                extraction_method="AUDIO_PROCESSING_ERROR",
                success=False,
                error_message=f"Audio processing failure: {str(e)}",
                is_meaningful=False,
            )
