import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles
from app.models.claim import Claim
from app.models.contradiction import Contradiction
from app.services.contradiction_service import ContradictionService


@pytest.mark.asyncio
async def test_contradiction_free_story(db_session: AsyncSession):
    """Test 1: Clear story without contradictory claims allows predictions."""
    src = Source(id="src-clear-01", name="Wire A", domain="wire-a.com", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add(src)
    await db_session.flush()

    art = Article(
        id="art-clear-01",
        source_id=src.id,
        title="State Pollution Control Board initiates scheduled compliance review",
        url="https://wire-a.com/review",
        published_at=datetime.now(timezone.utc),
        language="en",
        excerpt="Officials confirmed the annual compliance review began on Monday morning.",
        attribution_text="Wire A",
    )
    db_session.add(art)
    await db_session.flush()

    story = Story(id="story-clear-01", title="Annual Compliance Review", status="EMERGING")
    db_session.add(story)
    await db_session.flush()

    gate_res = await ContradictionService.evaluate_contradiction_gate(
        db=db_session,
        story_id=story.id,
        articles=[art],
    )

    assert gate_res.contradiction_status == "CLEAR"
    assert gate_res.prediction_eligible is True
    assert gate_res.is_halted is False
    assert gate_res.load_bearing_conflicts_count == 0


@pytest.mark.asyncio
async def test_load_bearing_contradiction_hard_gate(db_session: AsyncSession):
    """Test 3 & 4: Load-bearing conflict (e.g. approved vs rejected) strictly blocks prediction even if 8 vs 2."""
    src_a = Source(id="src-conf-a", name="National Herald", domain="herald.in", source_type="REGIONAL_MEDIA", primary_language="en")
    src_b = Source(id="src-conf-b", name="Business Standard", domain="bs.in", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src_a, src_b])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Source A claims expansion approved
    art_a = Article(
        id="art-conf-a",
        source_id=src_a.id,
        title="Regulator confirmed: Company X manufacturing expansion approved",
        url="https://herald.in/expansion-approved",
        published_at=now,
        language="en",
        excerpt="Official statement from State Board: Company X plant expansion approved following review.",
        attribution_text="National Herald",
    )
    # Source B claims expansion rejected
    art_b = Article(
        id="art-conf-b",
        source_id=src_b.id,
        title="Regulator confirmed: Company X manufacturing expansion rejected",
        url="https://bs.in/expansion-rejected",
        published_at=now,
        language="en",
        excerpt="Official statement from State Board: Company X plant expansion rejected due to environmental concerns.",
        attribution_text="Business Standard",
    )
    db_session.add_all([art_a, art_b])
    await db_session.flush()

    story = Story(id="story-conf-01", title="Company X Expansion Status Review", status="EMERGING")
    db_session.add(story)
    await db_session.flush()

    # Evaluate Contradiction Gate
    gate_res = await ContradictionService.evaluate_contradiction_gate(
        db=db_session,
        story_id=story.id,
        articles=[art_a, art_b],
    )

    # MUST strictly block prediction
    assert gate_res.contradiction_status == "PREDICTION_BLOCKED"
    assert gate_res.prediction_eligible is False
    assert gate_res.is_halted is True
    assert gate_res.load_bearing_conflicts_count >= 1
    assert len(gate_res.contradictions) >= 1
    assert gate_res.contradictions[0].is_load_bearing is True
    assert gate_res.contradictions[0].status == "OPEN"


@pytest.mark.asyncio
async def test_resolve_contradiction_api_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test 5: Analyst resolution of a contradiction unblocks prediction eligibility."""
    src_a = Source(id="src-res-a", name="Source A", domain="a.org", source_type="REGIONAL_MEDIA", primary_language="en")
    src_b = Source(id="src-res-b", name="Source B", domain="b.org", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src_a, src_b])
    await db_session.flush()

    art_a = Article(id="art-res-a", source_id=src_a.id, title="Plant approved", url="https://a.org/app", published_at=datetime.now(timezone.utc), language="en", excerpt="Plant approved", attribution_text="Source A")
    art_b = Article(id="art-res-b", source_id=src_b.id, title="Plant rejected", url="https://b.org/rej", published_at=datetime.now(timezone.utc), language="en", excerpt="Plant rejected", attribution_text="Source B")
    db_session.add_all([art_a, art_b])
    await db_session.flush()

    story = Story(id="story-res-01", title="Plant Status", status="EMERGING")
    db_session.add(story)
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art_a.id))
    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art_b.id))
    await db_session.commit()

    # Evaluate gate to generate contradiction record
    gate_res = await ContradictionService.evaluate_contradiction_gate(db_session, story.id, [art_a, art_b])
    assert gate_res.prediction_eligible is False
    contradiction_id = gate_res.contradictions[0].id
    await db_session.commit()

    # Call Resolution Endpoint
    resp = await client.post(
        f"/api/v1/stories/{story.id}/contradictions/{contradiction_id}/resolve",
        json={"resolution_notes": "Official gazette confirms approval; Source B retracted their earlier report."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["prediction_eligible"] is True

    # Verify Story record updated
    res_story = await db_session.execute(
        select(Story).where(Story.id == story.id).execution_options(populate_existing=True)
    )
    updated_story = res_story.scalars().first()
    assert updated_story.prediction_eligible is True
    assert updated_story.contradiction_status in ["CLEAR", "RESOLVED"]
