import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.media import (
    Media,
    MediaProcessingJob,
    MediaExtraction,
    MediaTypeEnum,
    MediaProcessingStatusEnum,
)
from app.services.media_service import MediaService


@pytest.mark.asyncio
async def test_media_model_creation_and_status_lifecycle(db_session: AsyncSession):
    """Verify that Media entity supports all media types and processing status transitions."""
    # 1. Create Media record via service
    media = await MediaService.create_media_record(
        db=db_session,
        original_filename="regulatory_filing_2026.pdf",
        mime_type="application/pdf",
        file_size_bytes=1048576,
        storage_reference="/uploads/regulatory_filing_2026.pdf",
        source_metadata={"submitter": "investigative_desk_01"},
    )
    assert media.id is not None
    assert media.media_type == MediaTypeEnum.PDF.value
    assert media.processing_status == MediaProcessingStatusEnum.UPLOADED.value

    # 2. Transition status: UPLOADED -> QUEUED
    media = await MediaService.update_processing_status(
        db=db_session,
        media_id=media.id,
        status=MediaProcessingStatusEnum.QUEUED,
    )
    assert media.processing_status == MediaProcessingStatusEnum.QUEUED.value

    # 3. Create MediaProcessingJob
    job = MediaProcessingJob(
        media_id=media.id,
        job_type="OCR_TEXT_EXTRACTION",
        status="QUEUED",
        job_metadata={"priority": "high"},
    )
    db_session.add(job)
    await db_session.flush()
    assert job.id is not None

    # 4. Transition status: QUEUED -> PROCESSING
    media = await MediaService.update_processing_status(
        db=db_session,
        media_id=media.id,
        status=MediaProcessingStatusEnum.PROCESSING,
    )
    assert media.processing_status == MediaProcessingStatusEnum.PROCESSING.value

    # 5. Create MediaExtraction record
    extraction = MediaExtraction(
        media_id=media.id,
        extraction_type="OCR_TEXT",
        extracted_text="State Environmental Protection Authority Order No. 441",
        extracted_entities=["State Environmental Protection Authority", "Order No. 441"],
        confidence_score=0.98,
    )
    db_session.add(extraction)
    await db_session.flush()
    assert extraction.id is not None

    # 6. Transition status: PROCESSING -> COMPLETED
    media = await MediaService.update_processing_status(
        db=db_session,
        media_id=media.id,
        status=MediaProcessingStatusEnum.COMPLETED,
    )
    assert media.processing_status == MediaProcessingStatusEnum.COMPLETED.value

    # 7. Test FAILED status with error logging
    failed_media = await MediaService.create_media_record(
        db=db_session,
        original_filename="corrupted_audio.wav",
        mime_type="audio/wav",
        file_size_bytes=2048,
        storage_reference="/uploads/corrupted_audio.wav",
    )
    failed_media = await MediaService.update_processing_status(
        db=db_session,
        media_id=failed_media.id,
        status=MediaProcessingStatusEnum.FAILED,
        error="Invalid audio header / corrupt container format.",
    )
    assert failed_media.processing_status == MediaProcessingStatusEnum.FAILED.value
    assert failed_media.processing_error == "Invalid audio header / corrupt container format."
