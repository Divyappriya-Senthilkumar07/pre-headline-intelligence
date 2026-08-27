import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.media import (
    Media,
    MediaProcessingJob,
    MediaExtraction,
    MediaTypeEnum,
    MediaProcessingStatusEnum,
)
from app.models.article import Article
from app.models.source import Source, SourceProfile
from app.services.extractors import (
    TextExtractor,
    PdfExtractor,
    ImageExtractor,
    AudioExtractor,
    VideoExtractor,
    ExtractionResult,
)
from app.services.deduplication import DeduplicationService

logger = logging.getLogger(__name__)


class MediaProcessor:
    """
    Media Ingestion & Processing Orchestrator.
    Handles the state machine: UPLOADED -> QUEUED -> PROCESSING -> COMPLETED / FAILED.
    Dispatches to appropriate type extractors and creates normalized Article records when meaningful.
    """

    def __init__(self):
        self.text_extractor = TextExtractor()
        self.pdf_extractor = PdfExtractor()
        self.image_extractor = ImageExtractor()
        self.audio_extractor = AudioExtractor()
        self.video_extractor = VideoExtractor()

    async def process_media(self, db: AsyncSession, media_id: str) -> Media:
        """
        Executes end-to-end media extraction and updates database records.
        """
        # 1. Fetch Media record
        result = await db.execute(select(Media).where(Media.id == media_id))
        media = result.scalars().first()
        if not media:
            raise ValueError(f"Media with id {media_id} not found.")

        # 2. Transition state: QUEUED -> PROCESSING
        media.processing_status = MediaProcessingStatusEnum.PROCESSING.value
        media.processing_error = None
        
        job = MediaProcessingJob(
            id=str(uuid.uuid4()),
            media_id=media.id,
            job_type=f"{media.media_type}_EXTRACTION",
            status="PROCESSING",
            job_metadata={"storage_path": media.storage_reference},
        )
        db.add(job)
        await db.commit()
        await db.refresh(media)

        logger.info(f"[MediaProcessor] Processing media {media.id} ({media.original_filename}, type={media.media_type})")

        # 3. Dispatch to extractor based on media type
        try:
            extraction_result: ExtractionResult
            if media.media_type == MediaTypeEnum.TEXT.value:
                extraction_result = await self.text_extractor.extract(
                    media.storage_reference, media.mime_type, media.original_filename
                )
            elif media.media_type == MediaTypeEnum.PDF.value:
                extraction_result = await self.pdf_extractor.extract(
                    media.storage_reference, media.mime_type, media.original_filename
                )
            elif media.media_type == MediaTypeEnum.IMAGE.value:
                extraction_result = await self.image_extractor.extract(
                    media.storage_reference, media.mime_type, media.original_filename
                )
            elif media.media_type == MediaTypeEnum.AUDIO.value:
                extraction_result = await self.audio_extractor.extract(
                    media.storage_reference, media.mime_type, media.original_filename
                )
            elif media.media_type == MediaTypeEnum.VIDEO.value:
                extraction_result = await self.video_extractor.extract(
                    media.storage_reference, media.mime_type, media.original_filename
                )
            else:
                extraction_result = ExtractionResult(
                    extraction_method="UNSUPPORTED_MEDIA",
                    success=False,
                    error_message=f"Unsupported media type: {media.media_type}",
                )

            # 4. Save MediaExtraction record
            extraction = MediaExtraction(
                id=str(uuid.uuid4()),
                media_id=media.id,
                extraction_type=extraction_result.extraction_method,
                extracted_text=extraction_result.extracted_text or None,
                extracted_entities=[],
                confidence_score=extraction_result.confidence,
                metadata_json={
                    **extraction_result.extracted_metadata,
                    "detected_language": extraction_result.detected_language,
                    "language_confidence": extraction_result.language_confidence,
                    "is_meaningful": extraction_result.is_meaningful,
                },
            )
            db.add(extraction)

            # 5. Handle success / failure state
            if extraction_result.success:
                media.processing_status = MediaProcessingStatusEnum.COMPLETED.value
                job.status = "COMPLETED"
                logger.info(f"[MediaProcessor] Successfully completed extraction for {media.id}")

                # 6. Normalized Article Creation if meaningful text exists
                if extraction_result.is_meaningful and extraction_result.extracted_text:
                    await self._create_normalized_article_from_media(db, media, extraction_result)

            else:
                media.processing_status = MediaProcessingStatusEnum.FAILED.value
                media.processing_error = extraction_result.error_message
                job.status = "FAILED"
                job.error_message = extraction_result.error_message
                logger.warning(f"[MediaProcessor] Media processing failed for {media.id}: {extraction_result.error_message}")

            await db.commit()
            await db.refresh(media)
            return media

        except Exception as e:
            logger.error(f"[MediaProcessor] Unhandled error processing media {media_id}: {e}", exc_info=True)
            media.processing_status = MediaProcessingStatusEnum.FAILED.value
            media.processing_error = str(e)
            job.status = "FAILED"
            job.error_message = str(e)
            await db.commit()
            await db.refresh(media)
            return media

    async def _create_normalized_article_from_media(
        self, db: AsyncSession, media: Media, extraction: ExtractionResult
    ) -> Optional[Article]:
        """
        Creates a normalized Article record from extracted media text.
        LEGAL REQUIREMENT: Store only short excerpts with attribution, never full text.
        """
        try:
            # Check or create default Analyst Upload Source
            source_res = await db.execute(select(Source).where(Source.name == "Analyst Direct Upload"))
            source = source_res.scalars().first()
            if not source:
                source = Source(
                    id=str(uuid.uuid4()),
                    name="Analyst Direct Upload",
                    domain="internal.pre-headline.ai",
                    source_type="ANALYST_UPLOAD",
                    primary_language=extraction.detected_language or "en",
                )
                db.add(source)
                await db.flush()

                profile = SourceProfile(
                    source_id=source.id,
                    independence_score=1.0,
                    reliability_score=0.95,
                )
                db.add(profile)
                await db.flush()

            # Create short excerpt only (first 300 chars max)
            full_text = extraction.extracted_text.strip()
            excerpt = full_text[:300] + ("..." if len(full_text) > 300 else "")
            
            # Title from original filename or first line
            first_line = full_text.splitlines()[0] if full_text.splitlines() else media.original_filename
            title = first_line[:150] if len(first_line) > 5 else f"Document: {media.original_filename}"

            canonical_url = f"media://{media.id}"
            
            # Check if article already exists for this media
            art_res = await db.execute(select(Article).where(Article.url == canonical_url))
            existing_art = art_res.scalars().first()
            if existing_art:
                return existing_art

            article = Article(
                id=str(uuid.uuid4()),
                source_id=source.id,
                title=title,
                url=canonical_url,
                published_at=media.upload_timestamp,
                language=extraction.detected_language or "en",
                excerpt=excerpt,
                attribution_text=f"Uploaded Document: {media.original_filename}",
                is_original_reporting=True,
                metadata_json={
                    "media_id": media.id,
                    "extraction_method": extraction.extraction_method,
                    "file_size_bytes": media.file_size_bytes,
                },
            )
            db.add(article)
            await db.flush()
            logger.info(f"[MediaProcessor] Created normalized Article {article.id} from media {media.id}")
            return article

        except Exception as err:
            logger.warning(f"[MediaProcessor] Failed to create normalized article for media {media.id}: {err}")
            return None
