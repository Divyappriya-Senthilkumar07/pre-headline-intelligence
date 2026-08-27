import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.services.rss_service import RssIngestionService

MOCK_RSS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>Tamil Nadu Daily News</title>
 <link>https://isolated-test-dinamalar.org</link>
 <description>Regional News Feed</description>
 <item>
  <title>அதிகாரிகள் தொழிற்சாலை ஆய்வு மேற்கொண்டனர்</title>
  <link>https://isolated-test-dinamalar.org/news/state-inspection-probe-2026</link>
  <description>தமிழக அரசு அதிகாரிகள் தீவிர விசாரணை நடத்தி வருகின்றனர்.</description>
  <pubDate>Wed, 26 Aug 2026 08:00:00 GMT</pubDate>
 </item>
 <item>
  <title>State Environmental Department Inspection Notice</title>
  <link>https://isolated-test-dinamalar.org/news/environmental-audit-notice</link>
  <description>Official inspection log published following plant visit.</description>
  <pubDate>Wed, 26 Aug 2026 08:30:00 GMT</pubDate>
 </item>
</channel>
</rss>
"""


@pytest.mark.asyncio
async def test_rss_feed_ingestion_and_deduplication(db_session: AsyncSession):
    """Test 10 & 11 & 13 & 14: RSS ingestion, source normalization, article creation, and duplicate prevention."""
    # First Ingestion Run
    stats1 = await RssIngestionService.ingest_feed(
        db=db_session,
        feed_url="https://isolated-test-dinamalar.org/rss/news_regional.xml",
        feed_name="Dinamalar Isolated Test",
        feed_content=MOCK_RSS_XML,
    )
    assert stats1["total_items"] == 2
    assert stats1["new_articles"] == 2
    assert stats1["duplicates_skipped"] == 0

    # Verify Source record
    source_res = await db_session.execute(select(Source).where(Source.domain == "isolated-test-dinamalar.org"))
    source = source_res.scalars().first()
    assert source is not None
    assert source.name == "Dinamalar Isolated Test"

    # Verify Article records
    art_res = await db_session.execute(select(Article).where(Article.source_id == source.id))
    articles = art_res.scalars().all()
    assert len(articles) == 2

    # Verify Tamil language detection and short excerpt
    tamil_art = next(a for a in articles if "ஆய்வு" in a.title)
    assert tamil_art.language == "ta"
    assert len(tamil_art.excerpt) <= 350
    assert "Dinamalar" in tamil_art.attribution_text

    # Second Ingestion Run with same XML -> MUST skip duplicates
    stats2 = await RssIngestionService.ingest_feed(
        db=db_session,
        feed_url="https://isolated-test-dinamalar.org/rss/news_regional.xml",
        feed_name="Dinamalar Isolated Test",
        feed_content=MOCK_RSS_XML,
    )
    assert stats2["new_articles"] == 0
    assert stats2["duplicates_skipped"] == 2


@pytest.mark.asyncio
async def test_rss_ingest_api_endpoint(client: AsyncClient):
    """Test POST /api/v1/ingest/rss endpoint."""
    resp = await client.post("/api/v1/ingest/rss")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "feeds_processed" in data
