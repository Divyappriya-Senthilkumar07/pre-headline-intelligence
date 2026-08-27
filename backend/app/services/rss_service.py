import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source, SourceProfile
from app.models.article import Article
from app.services.deduplication import DeduplicationService
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


DEFAULT_RSS_FEEDS = [
    {
        "name": "The Hindu - National",
        "url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "domain": "thehindu.com",
        "language": "en",
        "region": "India",
    },
    {
        "name": "Dinamalar - Tamil Regional",
        "url": "https://www.dinamalar.com/rss/news_regional.xml",
        "domain": "dinamalar.com",
        "language": "ta",
        "region": "Tamil Nadu",
    },
    {
        "name": "Dainik Bhaskar - Hindi National",
        "url": "https://www.bhaskar.com/rss-v1--all.xml",
        "domain": "bhaskar.com",
        "language": "hi",
        "region": "National",
    },
]


class RssIngestionService:
    """
    Automated RSS Feed Ingestion Service (Agent 1 — Discovery Component).
    Fetches, parses, normalizes, and deduplicates news signals into Article records.
    """

    @classmethod
    async def ingest_feed(
        cls,
        db: AsyncSession,
        feed_url: str,
        feed_name: Optional[str] = None,
        language: Optional[str] = None,
        feed_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingests a single RSS feed. Accepts optional feed_content for offline testing/mocking.
        """
        stats = {
            "feed_url": feed_url,
            "feed_name": feed_name or feed_url,
            "total_items": 0,
            "new_articles": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        # 1. Fetch feed content if not provided
        xml_text = feed_content
        if not xml_text:
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(feed_url, headers={"User-Agent": "PreHeadlineIntelligenceBot/1.0"})
                    if resp.status_code != 200:
                        logger.warning(f"Failed to fetch RSS feed {feed_url}: status {resp.status_code}")
                        stats["errors"] += 1
                        return stats
                    xml_text = resp.text
            except Exception as e:
                logger.error(f"Network error fetching RSS feed {feed_url}: {e}")
                stats["errors"] += 1
                return stats

        # 2. Parse RSS feed
        parsed = feedparser.parse(xml_text)
        if parsed.bozo and not parsed.entries:
            logger.warning(f"Malformed RSS feed at {feed_url}: {parsed.bozo_exception}")
            stats["errors"] += 1
            return stats

        # 3. Resolve / Create Source
        feed_title = feed_name or (parsed.feed.get("title") if hasattr(parsed, "feed") else None) or "RSS News Outlet"
        domain = DeduplicationService.normalize_url(feed_url).split("/")[2] if "://" in feed_url else "rss.source"

        source_res = await db.execute(select(Source).where(Source.domain == domain))
        source = source_res.scalars().first()
        if not source:
            source = Source(
                id=str(uuid.uuid4()),
                name=feed_title,
                domain=domain,
                source_type="RSS_FEED",
                primary_language=language or "en",
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

        stats["total_items"] = len(parsed.entries)

        # 4. Ingest articles
        for entry in parsed.entries:
            try:
                raw_url = entry.get("link", "")
                if not raw_url:
                    continue

                canonical_url = DeduplicationService.normalize_url(raw_url)
                
                # Check duplicate by URL
                existing_res = await db.execute(select(Article).where(Article.url == canonical_url))
                if existing_res.scalars().first():
                    stats["duplicates_skipped"] += 1
                    continue

                title = entry.get("title", "Untitled Signal").strip()
                summary_raw = entry.get("summary") or entry.get("description") or title
                
                # Clean html tags from summary
                import re
                clean_excerpt = re.sub(r"<[^>]+>", "", summary_raw).strip()
                # Legal compliance: Short excerpt only (max 350 chars)
                excerpt = clean_excerpt[:350] + ("..." if len(clean_excerpt) > 350 else "")

                # Parse published timestamp
                published_at = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    import time
                    published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)

                # Detect language
                detected_lang, _ = LanguageService.detect_language(f"{title} {excerpt}")
                final_lang = language or detected_lang or "en"

                article = Article(
                    id=str(uuid.uuid4()),
                    source_id=source.id,
                    title=title,
                    url=canonical_url,
                    published_at=published_at,
                    language=final_lang,
                    author=entry.get("author", None),
                    excerpt=excerpt,
                    attribution_text=f"Source: {feed_title}",
                    is_original_reporting=True,
                    metadata_json={
                        "rss_feed_url": feed_url,
                        "guid": entry.get("id", canonical_url),
                    },
                )
                db.add(article)
                stats["new_articles"] += 1

            except Exception as item_err:
                logger.debug(f"Error processing RSS entry: {item_err}")
                stats["errors"] += 1

        await db.commit()
        logger.info(f"[RssService] Ingested {stats['new_articles']} new articles from {feed_title} ({stats['duplicates_skipped']} dupes skipped)")
        return stats

    @classmethod
    async def ingest_all_configured_feeds(cls, db: AsyncSession, custom_feeds: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Runs ingestion across all registered feeds."""
        feeds = custom_feeds or DEFAULT_RSS_FEEDS
        results = []
        for f in feeds:
            res = await cls.ingest_feed(
                db=db,
                feed_url=f["url"],
                feed_name=f.get("name"),
                language=f.get("language"),
            )
            results.append(res)
        return results
