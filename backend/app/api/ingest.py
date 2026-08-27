from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.media import Media
from app.models.article import Article
from app.models.source import Source
from app.services.rss_service import RssIngestionService, DEFAULT_RSS_FEEDS, RSS_TELEMETRY
from app.services.gdelt_service import GdeltIngestionService, GDELT_TELEMETRY
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


@router.post("/gdelt", response_model=GdeltTriggerResponse, summary="Trigger GDELT Ingestion")
async def trigger_gdelt_ingestion(
    request: Optional[GdeltTriggerRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> GdeltTriggerResponse:
    """
    Retrieves real-time global news themes, entities, and sources from GDELT DOC 2.0 API.
    Normalizes entities and creates Article records without storing full text.
    """
    query_topic = request.query_topic if request else None
    result = await GdeltIngestionService.ingest_gkg_events(db, query_topic=query_topic)

    return GdeltTriggerResponse(
        status="success" if result.get("errors", 0) == 0 else "completed_with_warnings",
        total_records=result.get("total_records", 0),
        new_articles=result.get("new_articles", 0),
        new_entities=result.get("new_entities", 0),
        duplicates_skipped=result.get("duplicates_skipped", 0),
    )


@router.get("/status", response_model=IngestionDashboardResponse, summary="Get Ingestion Dashboard & Status")
async def get_ingestion_dashboard_status(db: AsyncSession = Depends(get_db)) -> IngestionDashboardResponse:
    """
    Returns aggregated ingestion health metrics, telemetry, recently ingested articles, and uploaded media.
    """
    # 1. Total Media count & recent media
    media_count_res = await db.execute(select(func.count(Media.id)))
    total_media = media_count_res.scalar() or 0

    recent_media_res = await db.execute(select(Media).order_by(Media.created_at.desc()).limit(5))
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
        select(Article).order_by(Article.published_at.desc()).limit(15)
    )
    recent_articles_db = recent_art_res.scalars().all()

    article_summaries = []
    is_live = False

    for art in recent_articles_db:
        # Check if live signal
        meta = art.metadata_json or {}
        if meta.get("gdelt_themes") or meta.get("rss_feed_url") or meta.get("socialimage") or not art.url.startswith("demo://"):
            is_live = True

        src_domain = None
        if "://" in art.url:
            src_domain = art.url.split("/")[2]

        article_summaries.append(
            IngestedArticleSummary(
                id=art.id,
                title=art.title,
                source_name=art.attribution_text,
                domain=src_domain,
                language=art.language or "en",
                published_at=art.published_at,
                excerpt=art.excerpt,
                url=art.url,
                social_image=meta.get("socialimage"),
            )
        )

    # Determine last successful ingestion timestamp
    last_ingestion = (
        GDELT_TELEMETRY.get("last_successful_ingestion")
        or RSS_TELEMETRY.get("last_successful_ingestion")
        or (recent_articles_db[0].published_at if recent_articles_db else None)
    )

    # Aggregate telemetry counts
    tot_fetched = GDELT_TELEMETRY.get("last_articles_fetched", 0) + RSS_TELEMETRY.get("last_articles_fetched", 0)
    tot_accepted = GDELT_TELEMETRY.get("last_articles_accepted", 0) + RSS_TELEMETRY.get("last_articles_accepted", 0)
    tot_dup = GDELT_TELEMETRY.get("last_duplicates_skipped", 0) + RSS_TELEMETRY.get("last_duplicates_skipped", 0)
    tot_err = GDELT_TELEMETRY.get("last_errors", 0) + RSS_TELEMETRY.get("last_errors", 0)

    gdelt_stat = GDELT_TELEMETRY.get("last_status", "ACTIVE")
    if gdelt_stat == "IDLE" and total_articles > 0:
        gdelt_stat = "ACTIVE"

    return IngestionDashboardResponse(
        source="GDELT_DOC_2.0 & RSS_FEEDS",
        current_status="ONLINE" if tot_err == 0 else "DEGRADED",
        rss_status="ACTIVE",
        gdelt_status=gdelt_stat,
        last_successful_ingestion=last_ingestion,
        total_articles_count=total_articles,
        total_sources_count=total_sources,
        articles_fetched=tot_fetched if tot_fetched > 0 else total_articles,
        articles_accepted=tot_accepted if tot_accepted > 0 else total_articles,
        duplicates_skipped=tot_dup,
        errors=tot_err,
        is_live_signal=is_live,
        total_media_count=total_media,
        recent_media=[MediaRead.model_validate(m) for m in recent_media],
        recent_articles=article_summaries,
    )
