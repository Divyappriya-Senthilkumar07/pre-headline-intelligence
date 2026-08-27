import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.media import Media, MediaProcessingJob, MediaExtraction, MediaTypeEnum, MediaProcessingStatusEnum
from app.schemas.media import MediaCreate, MediaRead

logger = logging.getLogger(__name__)


class MediaService:
    """
    Media Ingestion Foundation Service.
    Handles analyst-provided media ingestion records, storage references, and processing job tracking.
    NOTE: Heavy processing (OCR, transcription, video analysis) is intentionally scheduled for later phases.
    """

    @staticmethod
    def infer_media_type(mime_type: str, filename: str) -> MediaTypeEnum:
        mime = mime_type.lower()
        if mime.startswith("image/"):
            return MediaTypeEnum.IMAGE
        elif mime == "application/pdf" or filename.lower().endswith(".pdf"):
            return MediaTypeEnum.PDF
        elif mime.startswith("audio/"):
            return MediaTypeEnum.AUDIO
        elif mime.startswith("video/"):
            return MediaTypeEnum.VIDEO
        else:
            return MediaTypeEnum.TEXT

    @classmethod
    async def create_media_record(
        cls,
        db: AsyncSession,
        original_filename: str,
        mime_type: str,
        file_size_bytes: int,
        storage_reference: str,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> Media:
        media_type = cls.infer_media_type(mime_type, original_filename)
        
        media = Media(
            id=str(uuid.uuid4()),
            original_filename=original_filename,
            mime_type=mime_type,
            media_type=media_type.value,
            file_size_bytes=file_size_bytes,
            upload_timestamp=datetime.now(timezone.utc),
            processing_status=MediaProcessingStatusEnum.UPLOADED.value,
            storage_reference=storage_reference,
            source_metadata=source_metadata or {},
        )
        db.add(media)
        await db.commit()
        await db.refresh(media)
        logger.info(f"Created media record {media.id} for {original_filename} (type={media_type.value})")
        return media

    @classmethod
    async def get_media_by_id(cls, db: AsyncSession, media_id: str) -> Optional[Media]:
        result = await db.execute(select(Media).where(Media.id == media_id))
        return result.scalars().first()

    @classmethod
    async def list_media(cls, db: AsyncSession, limit: int = 50) -> List[Media]:
        result = await db.execute(select(Media).order_by(Media.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    @classmethod
    async def update_processing_status(
        cls,
        db: AsyncSession,
        media_id: str,
        status: MediaProcessingStatusEnum,
        error: Optional[str] = None,
    ) -> Optional[Media]:
        media = await cls.get_media_by_id(db, media_id)
        if media:
            media.processing_status = status.value
            if error:
                media.processing_error = error
            await db.commit()
            await db.refresh(media)
        return media
