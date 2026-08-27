import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Story
from app.models.alert import Alert


@pytest.mark.asyncio
async def test_feed_search_and_language_filtering(client: AsyncClient, db_session: AsyncSession):
    """Test 1 & 2: Search keyword matching and multilingual language filtering."""
    story_a = Story(
        id="story-flt-01",
        title="Chemical Emissions Investigation at Plant Beta",
        why_it_matters="Effluent review in progress.",
        formation_score=85.0,
        languages=["ta", "en"],
        status="EMERGING",
    )
    alert_a = Alert(
        id="alert-flt-01",
        story_id=story_a.id,
        title="Emerging: Chemical Emissions Investigation",
        headline_in_progress="Emerging: Chemical Emissions Investigation",
        why_it_matters="Effluent review in progress.",
        urgency=0.80,
        probability=0.85,
        impact=0.90,
        ranking_score=0.612,
        formation_score=85.0,
        independent_source_count=3,
        languages=["ta", "en"],
        status="ACTIVE",
    )

    story_b = Story(
        id="story-flt-02",
        title="Telecom Spectrum Allocation Notice",
        why_it_matters="Telecom policy updates.",
        formation_score=60.0,
        languages=["hi"],
        status="EMERGING",
    )
    alert_b = Alert(
        id="alert-flt-02",
        story_id=story_b.id,
        title="Emerging: Telecom Spectrum Allocation",
        headline_in_progress="Emerging: Telecom Spectrum Allocation",
        why_it_matters="Telecom policy updates.",
        urgency=0.50,
        probability=0.60,
        impact=0.50,
        ranking_score=0.150,
        formation_score=60.0,
        independent_source_count=2,
        languages=["hi"],
        status="ACTIVE",
    )

    db_session.add_all([story_a, alert_a, story_b, alert_b])
    await db_session.commit()

    # Search keyword match
    resp_search = await client.get("/api/v1/stories/emerging?search=Chemical")
    assert resp_search.status_code == 200
    items = resp_search.json()
    assert len(items) == 1
    assert items[0]["story_id"] == story_a.id

    # Filter by language
    resp_lang = await client.get("/api/v1/stories/emerging?language=hi")
    assert resp_lang.status_code == 200
    hi_items = resp_lang.json()
    assert len(hi_items) == 1
    assert hi_items[0]["story_id"] == story_b.id


@pytest.mark.asyncio
async def test_feed_sorting_and_threshold_filters(client: AsyncClient, db_session: AsyncSession):
    """Test 3: Threshold filtering and sorting options."""
    # Min formation score filter
    resp_thresh = await client.get("/api/v1/stories/emerging?min_formation_score=80")
    assert resp_thresh.status_code == 200
    high_score_items = resp_thresh.json()
    assert all(it["formation_score"] >= 80 for it in high_score_items)

    # Sort by independent sources
    resp_sort = await client.get("/api/v1/stories/emerging?sort_by=independent_sources")
    assert resp_sort.status_code == 200
    sorted_items = resp_sort.json()
    if len(sorted_items) >= 2:
        assert sorted_items[0]["independent_source_count"] >= sorted_items[1]["independent_source_count"]
