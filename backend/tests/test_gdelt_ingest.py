import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.models.graph import Entity
from app.services.gdelt_service import GdeltIngestionService

MOCK_GDELT_RECORDS = [
    {
        "url": "https://thehindu.com/news/state-regulatory-brief-2026",
        "title": "State pollution control board conducts scheduled regional audits",
        "seendate": "20260826T120000Z",
        "domain": "thehindu.com",
        "sourcecountry": "India",
        "language": "English",
        "themes": "ENV_REGULATORY;GOV_INSPECTION;COMPLIANCE",
        "organizations": "State Pollution Control Board;Company X",
        "locations": "Tamil Nadu, India",
    },
    {
        "url": "https://bhaskar.com/business/industrial-compliance-review",
        "title": "औद्योगिक अनुपालन समीक्षा पर क्षेत्रीय अधिकारियों का दौरा",
        "seendate": "20260826T121500Z",
        "domain": "bhaskar.com",
        "sourcecountry": "India",
        "language": "Hindi",
        "themes": "ENV_REGULATORY;MANUFACTURING",
        "organizations": "Company X",
        "locations": "India",
    },
]


@pytest.mark.asyncio
async def test_gdelt_gkg_ingestion_and_entity_mapping(db_session: AsyncSession):
    """Test 12 & 13 & 14: GDELT ingestion, entity extraction, and source normalization."""
    # First Ingestion
    stats1 = await GdeltIngestionService.ingest_gkg_events(
        db=db_session,
        mock_data=MOCK_GDELT_RECORDS,
    )
    assert stats1["total_records"] == 2
    assert stats1["new_articles"] == 2
    assert stats1["new_entities"] >= 1

    # Verify Entity record creation
    ent_res = await db_session.execute(select(Entity).where(Entity.name == "Company X"))
    entity = ent_res.scalars().first()
    assert entity is not None
    assert entity.entity_type in ["COMPANY", "ORGANIZATION"]

    # Verify Article records
    art_res = await db_session.execute(select(Article).where(Article.attribution_text.contains("GDELT")))
    articles = art_res.scalars().all()
    assert len(articles) == 2

    # Second Ingestion with same data -> MUST skip duplicates
    stats2 = await GdeltIngestionService.ingest_gkg_events(
        db=db_session,
        mock_data=MOCK_GDELT_RECORDS,
    )
    assert stats2["new_articles"] == 0
    assert stats2["duplicates_skipped"] == 2


@pytest.mark.asyncio
async def test_gdelt_timestamp_parsing():
    """Test GDELT timestamp parsing for multiple formats."""
    from app.services.gdelt_service import parse_gdelt_timestamp

    t1 = parse_gdelt_timestamp("20260827T021500Z")
    assert t1.year == 2026 and t1.month == 8 and t1.day == 27 and t1.hour == 2 and t1.minute == 15

    t2 = parse_gdelt_timestamp("20260827033000")
    assert t2.year == 2026 and t2.month == 8 and t2.day == 27 and t2.hour == 3 and t2.minute == 30

    t3 = parse_gdelt_timestamp("2026-08-27T04:45:00+00:00")
    assert t3.year == 2026 and t3.minute == 45

    t4 = parse_gdelt_timestamp(None)
    assert t4 is not None


def test_gdelt_query_formatting():
    """Test GDELT query formatting rules for boolean OR queries."""
    from app.services.gdelt_service import GdeltIngestionService

    q1 = GdeltIngestionService.format_query("climate OR energy")
    assert q1 == "(climate OR energy)"

    q2 = GdeltIngestionService.format_query("(technology OR climate)")
    assert q2 == "(technology OR climate)"

    q3 = GdeltIngestionService.format_query("climate")
    assert q3 == "climate"


@pytest.mark.asyncio
async def test_gdelt_deduplication_metadata_update(db_session: AsyncSession):
    """Test that duplicate articles update metadata rather than creating new records."""
    rec1 = [{
        "url": "https://reuters.com/business/energy-transition-report-2026",
        "title": "Global energy grid modernization accelerates",
        "seendate": "20260827T010000Z",
        "domain": "reuters.com",
        "language": "English",
        "socialimage": "",
    }]
    stats1 = await GdeltIngestionService.ingest_gkg_events(db=db_session, mock_data=rec1)
    assert stats1["new_articles"] == 1

    # Second ingestion provides socialimage
    rec2 = [{
        "url": "https://reuters.com/business/energy-transition-report-2026?utm_source=feed",
        "title": "Global energy grid modernization accelerates",
        "seendate": "20260827T010000Z",
        "domain": "reuters.com",
        "language": "English",
        "socialimage": "https://reuters.com/images/grid.jpg",
    }]
    stats2 = await GdeltIngestionService.ingest_gkg_events(db=db_session, mock_data=rec2)
    assert stats2["new_articles"] == 0
    assert stats2["duplicates_skipped"] == 1

    art_res = await db_session.execute(select(Article).where(Article.attribution_text.contains("reuters.com")))
    article = art_res.scalars().first()
    assert article is not None
    assert article.metadata_json.get("socialimage") == "https://reuters.com/images/grid.jpg"


@pytest.mark.asyncio
async def test_gdelt_ingest_api_endpoint(client: AsyncClient):
    """Test POST /api/v1/ingest/gdelt endpoint."""
    resp = await client.post("/api/v1/ingest/gdelt", json={"query_topic": "regulatory inspection"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["success", "completed_with_warnings"]
    assert "new_articles" in data


@pytest.mark.asyncio
async def test_ingest_dashboard_status_endpoint(client: AsyncClient):
    """Test GET /api/v1/ingest/status endpoint."""
    resp = await client.get("/api/v1/ingest/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_media_count" in data
    assert "total_articles_count" in data
    assert "rss_status" in data
    assert "gdelt_status" in data


@pytest.mark.asyncio
async def test_full_pipeline_execute_endpoint(client: AsyncClient):
    """Test POST /api/v1/pipeline/execute endpoint."""
    resp = await client.post("/api/v1/pipeline/execute")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["success", "empty_pipeline"]
    assert "stories_formed_count" in data
    assert "executed_at" in data

