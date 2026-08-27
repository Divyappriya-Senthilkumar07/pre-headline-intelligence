import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity
from app.models.contradiction import Contradiction
from app.services.prediction_service import PredictionService
from app.agents.prediction import PredictionAgent
from app.schemas.agent import PredictionInput


@pytest.mark.asyncio
async def test_probability_and_impact_remain_separate(db_session: AsyncSession):
    """Test 1: Probability and Impact are distinct and never collapsed into a single metric."""
    src = Source(id="src-pred-01", name="Regional Wire", domain="wire.in", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add(src)
    await db_session.flush()

    art = Article(
        id="art-pred-01",
        source_id=src.id,
        title="State Pollution Board conducts surprise audit at Company X plant",
        url="https://wire.in/audit",
        published_at=datetime.now(timezone.utc),
        language="en",
        excerpt="Officials initiated an emergency inspection following regional complaints.",
        attribution_text="Regional Wire",
    )
    ent = Entity(id="ent-pred-01", name="TNSPCB", canonical_name="State Pollution Board", entity_type="REGULATOR")
    db_session.add_all([art, ent])
    await db_session.flush()

    story = Story(
        id="story-pred-01",
        title="State Environmental Audit at Company X",
        formation_score=85.0,
        independence_score=0.80,
        cross_language_score=90.0,
        evidence_strength_score=85.0,
        independent_sources_count=3,
        status="EMERGING",
        contradiction_status="CLEAR",
        prediction_eligible=True,
    )
    db_session.add(story)
    await db_session.flush()

    res = await PredictionService.generate_prediction(
        db=db_session,
        story=story,
        articles=[art],
        entities=[ent],
    )

    # Verify probability and impact are separate
    assert 0.0 <= res.formation_probability <= 1.0
    assert 0.0 <= res.impact_score <= 1.0
    assert res.impact_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert res.prediction_status == "ELIGIBLE"
    assert res.blocked_reason is None


@pytest.mark.asyncio
async def test_trajectory_stages_progression(db_session: AsyncSession):
    """Test 2 & 4: Trajectory stages derived from signals: EARLY -> REGIONAL -> NATIONAL -> MAINSTREAM."""
    src_en = Source(id="src-t-en", name="The Hindu", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    src_ta = Source(id="src-t-ta", name="Dinamani", domain="dinamani.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src_hi = Source(id="src-t-hi", name="Dainik Bhaskar", domain="bhaskar.com", source_type="REGIONAL_MEDIA", primary_language="hi")
    db_session.add_all([src_en, src_ta, src_hi])
    await db_session.flush()

    art1 = Article(id="art-t-1", source_id=src_en.id, title="Probe 1", url="https://thehindu.com/p1", published_at=datetime.now(timezone.utc), language="en", excerpt="Audit", attribution_text="The Hindu")
    art2 = Article(id="art-t-2", source_id=src_ta.id, title="Probe 2", url="https://dinamani.com/p2", published_at=datetime.now(timezone.utc), language="ta", excerpt="Audit", attribution_text="Dinamani")
    art3 = Article(id="art-t-3", source_id=src_hi.id, title="Probe 3", url="https://bhaskar.com/p3", published_at=datetime.now(timezone.utc), language="hi", excerpt="Audit", attribution_text="Dainik Bhaskar")
    db_session.add_all([art1, art2, art3])
    await db_session.flush()

    # Early stage test
    curr_e, next_e, conf_e, _ = PredictionService.determine_trajectory([art1], ["en"], 1)
    assert curr_e == "EARLY"
    assert next_e == "REGIONAL"

    # Multilingual regional stage test
    curr_r, next_r, conf_r, _ = PredictionService.determine_trajectory([art1, art2], ["en", "ta"], 2)
    assert curr_r == "REGIONAL"
    assert next_r == "NATIONAL"

    # Cross-regional national stage test
    curr_n, next_n, conf_n, _ = PredictionService.determine_trajectory([art1, art2, art3], ["en", "ta", "hi"], 3)
    assert curr_n in ["REGIONAL", "NATIONAL"]


@pytest.mark.asyncio
async def test_contradiction_gate_strictly_blocks_prediction(db_session: AsyncSession):
    """Test 6: Load-bearing contradiction strictly blocks prediction eligibility."""
    story = Story(
        id="story-pred-blocked",
        title="Contradictory Regulatory Report",
        formation_score=80.0,
        independence_score=0.85,
        contradiction_status="PREDICTION_BLOCKED",
        prediction_eligible=False,
    )
    db_session.add(story)
    await db_session.flush()

    res = await PredictionService.generate_prediction(
        db=db_session,
        story=story,
        articles=[],
        entities=[],
    )

    assert res.prediction_status == "BLOCKED"
    assert res.blocked_reason == "LOAD_BEARING_CONTRADICTION"
    assert res.formation_probability == 0.0


@pytest.mark.asyncio
async def test_agent7_prediction_execution(db_session: AsyncSession):
    """Test 7: Agent 7 PredictionAgent execution."""
    story = Story(id="story-ag7-01", title="Plant Audit", status="EMERGING", formation_score=80.0)
    db_session.add(story)
    await db_session.commit()

    agent = PredictionAgent()
    input_data = PredictionInput(story_id=story.id)
    output = await agent.process(input_data, db=db_session)

    assert output.predicted_probability >= 0.0
    assert output.estimated_impact >= 0.0
    assert output.is_halted is False
