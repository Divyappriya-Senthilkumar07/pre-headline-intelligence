from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.media import Media
from app.models.article import Article
from app.models.source import Source
from app.services.rss_service import RssIngestionService, DEFAULT_RSS_FEEDS
from app.services.gdelt_service import GdeltIngestionService
from app.schemas.ingest import (
    RssTriggerRequest,
    RssTriggerResponse,
    GdeltTriggerRequest,
    GdeltTriggerResponse,
    IngestionDashboardResponse,
    IngestedArticleSummary,
)
from app.schemas.media import MediaRead

router = APIRouter(prefix="/ingest", tags=["Ingestion & Discovery Foundation"])


@router.post("/rss", response_model=RssTriggerResponse, summary="Trigger RSS Feed Ingestion")
async def trigger_rss_ingestion(
    request: Optional[RssTriggerRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> RssTriggerResponse:
    """
    Ingests candidate news signals from RSS feeds.
    Parses entries, extracts metadata, prevents duplicates, and creates normalized Article records.
    """
    custom_feeds = None
    if request and request.feed_url:
        custom_feeds = [{
            "url": request.feed_url,
            "name": request.feed_name or request.feed_url,
            "language": request.language or "en",
        }]

    results = await RssIngestionService.ingest_all_configured_feeds(db, custom_feeds=custom_feeds)
    
    total_new = sum(r.get("new_articles", 0) for r in results)
    total_dup = sum(r.get("duplicates_skipped", 0) for r in results)

    return RssTriggerResponse(
        status="success",
        feeds_processed=len(results),
        new_articles_total=total_new,
        duplicates_skipped_total=total_dup,
        details=results,
    )


@router.post("/gdelt", response_model=GdeltTriggerResponse, summary="Trigger GDELT GKG Ingestion")
async def trigger_gdelt_ingestion(
    request: Optional[GdeltTriggerRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> GdeltTriggerResponse:
    """
    Retrieves global news themes, entities, and sources from GDELT Global Knowledge Graph.
    Normalizes entities and creates Article records without storing full text.
    """
    query_topic = request.query_topic if request else None
    result = await GdeltIngestionService.ingest_gkg_events(db, query_topic=query_topic)

    return GdeltTriggerResponse(
        status="success",
        total_records=result.get("total_records", 0),
        new_articles=result.get("new_articles", 0),
        new_entities=result.get("new_entities", 0),
        duplicates_skipped=result.get("duplicates_skipped", 0),
    )


@router.get("/status", response_model=IngestionDashboardResponse, summary="Get Ingestion Dashboard & Status")
async def get_ingestion_dashboard_status(db: AsyncSession = Depends(get_db)) -> IngestionDashboardResponse:
    """
    Returns aggregated ingestion health metrics, recently uploaded media, and recent articles.
    """
    # 1. Total Media count & recent media
    media_count_res = await db.execute(select(func.count(Media.id)))
    total_media = media_count_res.scalar() or 0

    recent_media_res = await db.execute(select(Media).order_by(Media.created_at.desc()).limit(10))
    recent_media = recent_media_res.scalars().all()
    for m in recent_media:
        await db.refresh(m, ["extractions"])

    # 2. Total Articles & Sources
    art_count_res = await db.execute(select(func.count(Article.id)))
    total_articles = art_count_res.scalar() or 0

    src_count_res = await db.execute(select(func.count(Source.id)))
    total_sources = src_count_res.scalar() or 0

    # 3. Recent Articles
    recent_art_res = await db.execute(
        select(Article).order_by(Article.published_at.desc()).limit(10)
    )
    recent_articles_db = recent_art_res.scalars().all()

    article_summaries = [
        IngestedArticleSummary(
            id=art.id,
            title=art.title,
            source_name=art.attribution_text,
            language=art.language,
            published_at=art.published_at,
            excerpt=art.excerpt,
            url=art.url,
        )
        for art in recent_articles_db
    ]

    last_ingestion = recent_articles_db[0].published_at if recent_articles_db else None

    return IngestionDashboardResponse(
        total_media_count=total_media,
        recent_media=[MediaRead.model_validate(m) for m in recent_media],
        total_articles_count=total_articles,
        total_sources_count=total_sources,
        rss_status="ACTIVE",
        gdelt_status="ACTIVE",
        last_successful_ingestion=last_ingestion,
        recent_articles=article_summaries,
    )
