import os
import re
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.models.media import Media, MediaProcessingStatusEnum, MediaTypeEnum
from app.services.media_service import MediaService
from app.services.media_processor import MediaProcessor
from app.schemas.media import (
    MediaRead,
    MediaUploadResponse,
    MediaStatusResponse,
    MediaDeleteResponse,
    MediaRetryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["Media Ingestion Foundation"])

# Security whitelists
ALLOWED_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp", ".bmp",
    # Documents
    ".pdf", ".txt", ".md", ".csv", ".json", ".rtf",
    # Audio
    ".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac",
    # Video
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".py", ".js", ".vbs", ".dll", ".so", ".bin", ".app", ".msi"
}

ALLOWED_MIME_PREFIXES = ["image/", "application/pdf", "text/", "audio/", "video/"]
MAX_FILE_SIZE_BYTES = settings.MEDIA_MAX_FILE_SIZE_MB * 1024 * 1024


async def _run_media_processing_task(media_id: str):
    """Background execution runner for media extraction."""
    async with AsyncSessionLocal() as session:
        try:
            processor = MediaProcessor()
            await processor.process_media(session, media_id)
        except Exception as e:
            logger.error(f"Background media processor error for {media_id}: {e}", exc_info=True)


@router.post(
    "/upload",
    response_model=MediaUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Analyst Media",
    description="Uploads media files (Images, PDFs, Text, Audio, Video), validates security constraints, and queues extraction.",
)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> MediaUploadResponse:
    # 1. Validation: File presence & filename
    if not file or not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided.")

    original_filename = os.path.basename(file.filename)
    name, ext = os.path.splitext(original_filename)
    ext_lower = ext.lower()

    # 2. Security validation: Extension check
    if ext_lower in BLOCKED_EXTENSIONS or (ext_lower not in ALLOWED_EXTENSIONS and not file.content_type.startswith("text/")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported or restricted file extension '{ext}'. Allowed types: images, PDFs, text files, audio, video.",
        )

    # 3. Security validation: MIME check
    mime_type = file.content_type or "application/octet-stream"
    if not any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES) and ext_lower != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported MIME type '{mime_type}'.",
        )

    # 4. Read content & validate file size
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MEDIA_MAX_FILE_SIZE_MB}MB.",
        )

    # 5. Store file securely
    os.makedirs(settings.MEDIA_STORAGE_PATH, exist_ok=True)
    safe_storage_name = f"{uuid.uuid4().hex}{ext_lower}"
    storage_path = os.path.join(settings.MEDIA_STORAGE_PATH, safe_storage_name)

    with open(storage_path, "wb") as f:
        f.write(content)

    # 6. Create Media record in DB
    media = await MediaService.create_media_record(
        db=db,
        original_filename=original_filename,
        mime_type=mime_type,
        file_size_bytes=file_size,
        storage_reference=storage_path,
        source_metadata={"analyst_notes": notes} if notes else {},
    )

    # 7. Execute processing
    # For small text/pdf/images in development, process synchronously or via background tasks
    processor = MediaProcessor()
    processed_media = await processor.process_media(db, media.id)

    return MediaUploadResponse(
        id=processed_media.id,
        filename=processed_media.original_filename,
        media_type=processed_media.media_type,
        mime_type=processed_media.mime_type,
        size=processed_media.file_size_bytes,
        processing_status=processed_media.processing_status,
        created_at=processed_media.upload_timestamp,
        message="Media uploaded and processed through extraction pipeline.",
    )


@router.get(
    "/{media_id}/status",
    response_model=MediaStatusResponse,
    summary="Get Media Processing Status",
    description="Real-time status check for extraction progress and current processing step.",
)
async def get_media_status(media_id: str, db: AsyncSession = Depends(get_db)) -> MediaStatusResponse:
    media = await MediaService.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media {media_id} not found.")

    is_completed = media.processing_status == MediaProcessingStatusEnum.COMPLETED.value
    is_failed = media.processing_status == MediaProcessingStatusEnum.FAILED.value

    progress = 100 if is_completed else (0 if media.processing_status == "UPLOADED" else (50 if media.processing_status == "PROCESSING" else 0))
    current_step = "Extraction Completed" if is_completed else ("Processing Failed" if is_failed else f"Step: {media.processing_status}")

    return MediaStatusResponse(
        media_id=media.id,
        filename=media.original_filename,
        media_type=media.media_type,
        status=media.processing_status,
        progress_percent=progress,
        current_step=current_step,
        error_message=media.processing_error,
        created_at=media.upload_timestamp,
        is_completed=is_completed,
        is_failed=is_failed,
    )


@router.get(
    "/{media_id}",
    response_model=MediaRead,
    summary="Get Media and Extractions Detail",
)
async def get_media_detail(media_id: str, db: AsyncSession = Depends(get_db)) -> MediaRead:
    # Eager load extractions
    result = await db.execute(
        select(Media).where(Media.id == media_id)
    )
    media = result.scalars().first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media {media_id} not found.")
    
    # Refresh relations
    await db.refresh(media, ["extractions"])
    return MediaRead.model_validate(media)


@router.delete(
    "/{media_id}",
    response_model=MediaDeleteResponse,
    summary="Delete Uploaded Media",
    description="Safely removes stored file from disk and deletes DB media record.",
)
async def delete_media(media_id: str, db: AsyncSession = Depends(get_db)) -> MediaDeleteResponse:
    media = await MediaService.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media {media_id} not found.")

    # Remove file from disk if present
    if media.storage_reference and os.path.exists(media.storage_reference):
        try:
            os.remove(media.storage_reference)
        except Exception as e:
            logger.warning(f"Could not delete physical file {media.storage_reference}: {e}")

    await db.delete(media)
    await db.commit()

    return MediaDeleteResponse(
        media_id=media_id,
        success=True,
        message=f"Media {media_id} and associated extractions successfully deleted.",
    )


@router.post(
    "/{media_id}/retry",
    response_model=MediaRetryResponse,
    summary="Retry Failed Media Processing",
)
async def retry_media_processing(
    media_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MediaRetryResponse:
    media = await MediaService.get_media_by_id(db, media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media {media_id} not found.")

    # Reset state and re-process
    media.processing_status = MediaProcessingStatusEnum.QUEUED.value
    media.processing_error = None
    await db.commit()

    processor = MediaProcessor()
    await processor.process_media(db, media_id)

    return MediaRetryResponse(
        media_id=media_id,
        status="RETRY_TRIGGERED",
        message="Media processing re-triggered successfully.",
    )


@router.get(
    "",
    response_model=List[MediaRead],
    summary="List Uploaded Media",
)
async def list_media(limit: int = 50, db: AsyncSession = Depends(get_db)) -> List[MediaRead]:
    res = await db.execute(select(Media).order_by(Media.created_at.desc()).limit(limit))
    media_list = res.scalars().all()
    for m in media_list:
        await db.refresh(m, ["extractions"])
    return [MediaRead.model_validate(m) for m in media_list]
