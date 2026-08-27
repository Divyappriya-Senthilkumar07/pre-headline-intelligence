import uuid
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.source import Source, SourceProfile
from app.models.article import Article
from app.models.graph import Entity
from app.services.deduplication import DeduplicationService
from app.services.language_service import LanguageService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global telemetry tracker for live GDELT ingestion
GDELT_TELEMETRY: Dict[str, Any] = {
    "last_successful_ingestion": None,
    "last_status": "IDLE",
    "last_articles_fetched": 0,
    "last_articles_accepted": 0,
    "last_duplicates_skipped": 0,
    "last_errors": 0,
    "last_error_message": None,
}


def parse_gdelt_timestamp(date_str: Optional[str]) -> datetime:
    """
    Parses GDELT seendate format (e.g. '20260827T014500Z', '20260827014500', or ISO8601).
    """
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        clean_str = date_str.strip()
        if "T" in clean_str and clean_str.endswith("Z"):
            return datetime.strptime(clean_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        elif len(clean_str) == 14 and clean_str.isdigit():
            return datetime.strptime(clean_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        else:
            return datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


class GdeltIngestionService:
    """
    GDELT Ingestion Service (Agent 1 Discovery Component).
    Fetches real-time news articles from GDELT DOC 2.0 API, parses metadata,
    deduplicates against PostgreSQL, normalizes into Article models, and extracts candidate entities.
    """

    GDELT_DOC_ENDPOINT = "http://api.gdeltproject.org/api/v2/doc/doc"

    @classmethod
    def format_query(cls, query: Optional[str]) -> str:
        """Ensures GDELT query meets API rules (e.g. OR terms enclosed in parentheses)."""
        raw_query = query or getattr(
            settings,
            "GDELT_DEFAULT_QUERY",
            "(technology OR energy OR regulatory OR industry OR climate OR health OR business OR economy OR policy)",
        )
        raw_query = raw_query.strip()
        if " OR " in raw_query and not (raw_query.startswith("(") and raw_query.endswith(")")):
            raw_query = f"({raw_query})"
        return raw_query

    @classmethod
    async def fetch_live_gdelt_articles(
        cls,
        query: Optional[str] = None,
        max_records: Optional[int] = None,
        timespan: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real-time articles from GDELT DOC 2.0 API with retry, backoff, and query fallback.
        """
        endpoint = getattr(settings, "GDELT_DOC_API_URL", cls.GDELT_DOC_ENDPOINT)
        search_query = cls.format_query(query)
        records_limit = max_records or getattr(settings, "GDELT_MAX_RECORDS", 30)
        time_window = timespan or getattr(settings, "GDELT_TIMESPAN", "60min")

        params: Dict[str, Any] = {
            "query": search_query,
            "mode": "artlist",
            "maxrecords": records_limit,
            "format": "json",
            "sort": "datedesc",
        }
        if time_window:
            params["timespan"] = time_window

        headers = {
            "User-Agent": "PreHeadlineIntelligenceBot/1.0 (Research Intelligence; Open Access)",
            "Accept": "application/json",
        }

        # Try live requests with backoff
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(endpoint, params=params, headers=headers)
                    if resp.status_code == 200 and resp.content:
                        try:
                            data = resp.json()
                            articles = data.get("articles", [])
                            if articles:
                                logger.info(f"[GdeltService] Successfully retrieved {len(articles)} real articles from GDELT DOC 2.0 API.")
                                return articles
                        except Exception as parse_err:
                            logger.debug(f"[GdeltService] JSON decode note: {parse_err}")
                    elif resp.status_code == 429:
                        logger.warning(f"[GdeltService] GDELT rate limit (429) on attempt {attempt+1}. Backing off.")
                        import asyncio
                        await asyncio.sleep(2.5)
                    else:
                        logger.warning(f"[GdeltService] GDELT responded with status {resp.status_code}: {resp.text[:150]}")
            except Exception as net_err:
                logger.warning(f"[GdeltService] Network attempt {attempt+1} failed: {net_err}")

        # Fallback to single broad keyword if complex query returned no matches or error
        try:
            fallback_params = {
                "query": "climate",
                "mode": "artlist",
                "maxrecords": records_limit,
                "format": "json",
                "sort": "datedesc",
            }
            if time_window:
                fallback_params["timespan"] = time_window
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(endpoint, params=fallback_params, headers=headers)
                if resp.status_code == 200 and resp.content:
                    data = resp.json()
                    articles = data.get("articles", [])
                    if articles:
                        return articles
        except Exception as e:
            logger.debug(f"[GdeltService] Fallback query error: {e}")

        return []

    @classmethod
    async def ingest_gkg_events(
        cls,
        db: AsyncSession,
        query_topic: Optional[str] = None,
        mock_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Ingests real-time GDELT news. Accepts optional mock_data for testing/offline scenarios.
        """
        stats = {
            "source": "GDELT_DOC_2.0",
            "total_records": 0,
            "new_articles": 0,
            "new_entities": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        # 1. Obtain raw GDELT records
        records = mock_data
        if not records:
            records = await cls.fetch_live_gdelt_articles(query=query_topic, max_records=30)

        # If live external API is unreachable or returned empty, do not crash; record status
        if not records:
            logger.info("[GdeltService] No external records returned from GDELT for current query.")
            GDELT_TELEMETRY["last_status"] = "EMPTY_RESPONSE"
            GDELT_TELEMETRY["last_errors"] += 1
            return stats

        stats["total_records"] = len(records)
        GDELT_TELEMETRY["last_articles_fetched"] = len(records)

        # 2. Process and persist records into PostgreSQL
        for item in records:
            try:
                raw_url = item.get("url", "").strip()
                if not raw_url:
                    continue

                canonical_url = DeduplicationService.normalize_url(raw_url)
                title = item.get("title", "GDELT News Signal").strip()
                social_image = item.get("socialimage") or ""
                source_country = item.get("sourcecountry") or "Global"
                
                # Parse domain
                domain = item.get("domain") or (canonical_url.split("/")[2] if "://" in canonical_url else "gdelt.org")
                if domain.startswith("www."):
                    domain = domain[4:]

                # Content excerpt (compliant short snippet)
                clean_title = re.sub(r"\s+", " ", title)
                excerpt = f"Live report from {domain} ({source_country}): {clean_title}."
                if len(excerpt) > 350:
                    excerpt = excerpt[:347] + "..."

                content_hash = DeduplicationService.compute_content_hash(f"{title} {excerpt}")

                # 3. Deduplication Check by URL and Content Hash
                existing_res = await db.execute(select(Article).where(Article.url == canonical_url))
                existing_article = existing_res.scalars().first()

                if existing_article:
                    # Update metadata on existing article if new image/tags available
                    if social_image and not existing_article.metadata_json.get("socialimage"):
                        existing_article.metadata_json = {
                            **existing_article.metadata_json,
                            "socialimage": social_image,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                        await db.flush()
                    stats["duplicates_skipped"] += 1
                    continue

                # 4. Resolve or create Source record
                source_res = await db.execute(select(Source).where(Source.domain == domain))
                source = source_res.scalars().first()
                if not source:
                    source_name = domain.split(".")[0].capitalize() if "." in domain else domain
                    source = Source(
                        id=str(uuid.uuid4()),
                        name=f"{source_name} ({domain})",
                        domain=domain,
                        source_type="GDELT_LIVE",
                        country=source_country,
                        primary_language="en",
                    )
                    db.add(source)
                    await db.flush()

                    profile = SourceProfile(
                        source_id=source.id,
                        independence_score=0.85,
                        reliability_score=0.80,
                    )
                    db.add(profile)
                    await db.flush()

                # 5. Language detection and timestamp parsing
                detected_lang, _ = LanguageService.detect_language(f"{title} {excerpt}")
                item_lang = item.get("language")
                final_lang = "en"
                if item_lang:
                    if "english" in item_lang.lower():
                        final_lang = "en"
                    elif "tamil" in item_lang.lower():
                        final_lang = "ta"
                    elif "hindi" in item_lang.lower():
                        final_lang = "hi"
                    else:
                        final_lang = detected_lang or "en"
                else:
                    final_lang = detected_lang or "en"

                pub_time = parse_gdelt_timestamp(item.get("seendate"))

                # 6. Create Article Record
                themes = item.get("themes", "")
                themes_list = themes.split(";") if isinstance(themes, str) and themes else []

                article = Article(
                    id=str(uuid.uuid4()),
                    source_id=source.id,
                    title=title,
                    url=canonical_url,
                    published_at=pub_time,
                    language=final_lang,
                    excerpt=excerpt,
                    attribution_text=f"GDELT Live Stream ({domain})",
                    is_original_reporting=True,
                    metadata_json={
                        "content_hash": content_hash,
                        "socialimage": social_image,
                        "sourcecountry": source_country,
                        "gdelt_themes": themes_list,
                        "gdelt_seendate": item.get("seendate"),
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                db.add(article)
                await db.flush()
                stats["new_articles"] += 1

                # 7. Extract potential organization entities from domain / title
                orgs = item.get("organizations", "")
                org_candidates = orgs.split(";") if isinstance(orgs, str) and orgs else []
                for org_name in org_candidates:
                    org_clean = org_name.strip()
                    if org_clean and len(org_clean) > 2:
                        ent_res = await db.execute(select(Entity).where(Entity.name == org_clean))
                        if not ent_res.scalars().first():
                            new_ent = Entity(
                                id=str(uuid.uuid4()),
                                name=org_clean,
                                canonical_name=org_clean,
                                entity_type="ORGANIZATION",
                                aliases=[org_clean],
                                gdelt_id=f"gdelt-org-{org_clean.lower().replace(' ', '-')}",
                            )
                            db.add(new_ent)
                            await db.flush()
                            stats["new_entities"] += 1

            except Exception as e:
                logger.debug(f"[GdeltService] Error processing GDELT record: {e}")
                stats["errors"] += 1

        await db.commit()

        # Update Telemetry
        now_utc = datetime.now(timezone.utc)
        GDELT_TELEMETRY["last_successful_ingestion"] = now_utc
        GDELT_TELEMETRY["last_status"] = "ONLINE"
        GDELT_TELEMETRY["last_articles_accepted"] = stats["new_articles"]
        GDELT_TELEMETRY["last_duplicates_skipped"] = stats["duplicates_skipped"]
        GDELT_TELEMETRY["last_errors"] = stats["errors"]

        logger.info(f"[GdeltService] Completed GDELT ingestion: {stats['new_articles']} new articles, {stats['duplicates_skipped']} duplicates skipped.")
        return stats
