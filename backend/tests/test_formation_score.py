import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity
from app.services.independence_service import IndependenceService
from app.services.contradiction_service import ContradictionService
from app.services.formation_service import StoryFormationService
from app.agents.formation import NarrativeFormationAgent
from app.schemas.agent import NarrativeFormationInput, IndependenceOutput


@pytest.mark.asyncio
async def test_six_dimension_explainable_formation_scoring(db_session: AsyncSession):
    """Test 1, 3, 5, 6: 6-Dimension formation score calculation grounded in actual story data."""
    src1 = Source(id="src-form-en", name="The Hindu", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    src2 = Source(id="src-form-ta", name="Dinamani", domain="dinamani.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src3 = Source(id="src-form-hi", name="Dainik Bhaskar", domain="bhaskar.com", source_type="REGIONAL_MEDIA", primary_language="hi")
    db_session.add_all([src1, src2, src3])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    art1 = Article(
        id="art-form-en",
        source_id=src1.id,
        title="State Pollution Control Board initiates compliance audit at Company X unit",
        url="https://thehindu.com/company-x",
        published_at=now,
        language="en",
        excerpt="Officials initiated compliance audit at Company X manufacturing plant.",
        attribution_text="The Hindu",
    )
    art2 = Article(
        id="art-form-ta",
        source_id=src2.id,
        title="கம்பெனி எக்ஸ் தொழிற்கூடத்தில் அதிகாரிகள் ஆய்வு",
        url="https://dinamani.com/company-x",
        published_at=now + timedelta(minutes=45),
        language="ta",
        excerpt="தமிழக அரசு மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு நடத்தினர்.",
        attribution_text="Dinamani",
    )
    art3 = Article(
        id="art-form-hi",
        source_id=src3.id,
        title="कंपनी एक्स संयंत्र में प्रदूषण नियंत्रण बोर्ड का औचक दौरा",
        url="https://bhaskar.com/company-x",
        published_at=now + timedelta(hours=2),
        language="hi",
        excerpt="प्रदूषण नियंत्रण बोर्ड के वरिष्ठ अधिकारियों ने पर्यावरण मानकों की जांच की।",
        attribution_text="Dainik Bhaskar",
    )
    db_session.add_all([art1, art2, art3])
    await db_session.flush()

    comp_x = Entity(id="ent-form-x", name="Company X", canonical_name="Company X", entity_type="COMPANY")
    regulator = Entity(id="ent-form-reg", name="TNSPCB", canonical_name="Tamil Nadu Pollution Control Board", entity_type="REGULATOR")
    db_session.add_all([comp_x, regulator])
    await db_session.flush()

    story = Story(
        id="story-formation-001",
        title="Environmental Audit & Regulatory Review at Company X",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art1.id))
    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art2.id))
    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art3.id))

    await db_session.execute(story_entities.insert().values(story_id=story.id, entity_id=comp_x.id))
    await db_session.execute(story_entities.insert().values(story_id=story.id, entity_id=regulator.id))
    await db_session.commit()

    # Run Independence and Contradiction Gate
    indep = await IndependenceService.analyze_story_independence(db_session, story.id, [art1, art2, art3], [comp_x, regulator])
    gate = await ContradictionService.evaluate_contradiction_gate(db_session, story.id, [art1, art2, art3])

    # Compute Formation Score
    formation_res = await StoryFormationService.compute_story_formation(
        db=db_session,
        story=story,
        articles=[art1, art2, art3],
        entities=[comp_x, regulator],
        independence=indep,
        contradiction_gate=gate,
    )

    # Verify 6 separate dimensions exist
    dims = formation_res.dimensions
    assert "source_diversity" in dims
    assert "temporal_spread" in dims
    assert "entity_alignment" in dims
    assert "cross_language_corroboration" in dims
    assert "evidence_strength" in dims
    assert "absence_of_contradictions" in dims

    # Verify weights
    assert dims["source_diversity"].weight_pct == 20
    assert dims["temporal_spread"].weight_pct == 15
    assert dims["entity_alignment"].weight_pct == 20
    assert dims["cross_language_corroboration"].weight_pct == 20
    assert dims["evidence_strength"].weight_pct == 15
    assert dims["absence_of_contradictions"].weight_pct == 10

    # Cross-language corroboration across 3 independent languages should be high
    assert dims["cross_language_corroboration"].score >= 90.0
    assert dims["absence_of_contradictions"].score == 100.0

    # Overall formation score should be high (CORROBORATED)
    assert formation_res.overall_score >= 75.0
    assert formation_res.formation_status == "CORROBORATED"
    assert formation_res.prediction_eligible is True

    # Verify grounded narrative mentions real entities and languages
    narrative = formation_res.narrative_summary
    assert "Company X" in narrative
    assert "3" in narrative  # independent sources
    assert "CLEAR" in narrative


@pytest.mark.asyncio
async def test_agent6_narrative_formation_execution(db_session: AsyncSession):
    """Test 2 & 4: Agent 6 NarrativeFormationAgent execution and persistence."""
    story = Story(id="story-agent6-01", title="Regional Probe at Factory", status="EMERGING")
    db_session.add(story)
    await db_session.commit()

    agent = NarrativeFormationAgent()
    input_data = NarrativeFormationInput(
        story_id=story.id,
        independence_data=IndependenceOutput(
            story_id=story.id,
            total_sources=2,
            independent_sources_count=2,
            independence_score=0.85,
        ),
    )

    output = await agent.process(input_data, db=db_session)
    assert output.formation_score >= 0.10
    assert output.dimensions.source_diversity >= 0.0
    assert len(output.narrative_summary) > 20
    assert "Ansoff" in output.framework_citation
