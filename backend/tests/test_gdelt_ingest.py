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
async def test_gdelt_ingest_api_endpoint(client: AsyncClient):
    """Test POST /api/v1/ingest/gdelt endpoint."""
    resp = await client.post("/api/v1/ingest/gdelt", json={"query_topic": "regulatory inspection"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
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
