import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert
from app.services.alert_service import AlertOrchestratorService
from app.agents.alert_orchestrator import AlertOrchestratorAgent
from app.schemas.agent import AlertOrchestratorInput, AlertCandidate


@pytest.mark.asyncio
async def test_alert_ranking_formula_and_separate_metrics(db_session: AsyncSession):
    """Test 1 & 2: Alert ranking = Urgency * Probability * Impact, with all components visible."""
    src = Source(id="src-alt-01", name="National Press", domain="natpress.com", source_type="REGIONAL_MEDIA", primary_language="en")
    art = Article(id="art-alt-01", source_id=src.id, title="Probe", url="https://natpress.com/p", published_at=datetime.now(timezone.utc), language="en", excerpt="Audit", attribution_text="National Press")
    db_session.add_all([src, art])
    await db_session.flush()

    story = Story(
        id="story-alt-01",
        title="Industrial Unit Emissions Investigation",
        formation_score=85.0,
        independent_sources_count=3,
        status="EMERGING",
        contradiction_status="CLEAR",
        prediction_eligible=True,
    )
    pred = Prediction(
        story_id=story.id,
        formation_probability=0.80,
        impact_score=0.90,
        impact_level="HIGH",
        current_stage="REGIONAL",
        predicted_next_stage="NATIONAL",
        prediction_status="ELIGIBLE",
    )
    chain = EvidenceChain(
        story_id=story.id,
        chain_status="COMPLETE",
        confidence_score=0.90,
        items=[{"step_order": 1, "source_name": "National Press", "claim_statement": "Probe ongoing", "evidence_type": "SOURCE_REPORT", "evidence_excerpt": "Quote"}],
    )
    db_session.add_all([story, pred, chain])
    await db_session.flush()

    alert = await AlertOrchestratorService.evaluate_and_create_alert(
        db=db_session,
        story=story,
        prediction=pred,
        evidence_chain=chain,
        articles=[art],
    )

    assert alert is not None
    assert alert.status == "ACTIVE"
    assert alert.probability == 0.80
    assert alert.impact == 0.90
    assert alert.urgency > 0.0
    # Verify ranking score equals urgency * probability * impact
    expected_rank = round(alert.urgency * alert.probability * alert.impact, 4)
    assert abs(alert.ranking_score - expected_rank) < 0.001


@pytest.mark.asyncio
async def test_missing_evidence_blocks_alert(db_session: AsyncSession):
    """Test 3: Missing evidence strictly blocks alert emission (No alert without evidence)."""
    story = Story(
        id="story-alt-no-ev",
        title="Unverified Rumor",
        formation_score=80.0,
        status="EMERGING",
        contradiction_status="CLEAR",
    )
    pred = Prediction(story_id=story.id, formation_probability=0.80, impact_score=0.70, prediction_status="ELIGIBLE")
    db_session.add_all([story, pred])
    await db_session.flush()

    # Null evidence chain
    alert = await AlertOrchestratorService.evaluate_and_create_alert(
        db=db_session,
        story=story,
        prediction=pred,
        evidence_chain=None,
        articles=[],
    )

    assert alert.status == "BLOCKED"
    assert "Insufficient structured evidence" in alert.ranking_explanation


@pytest.mark.asyncio
async def test_contradiction_gate_blocks_alert_emission(db_session: AsyncSession):
    """Test 4: Open load-bearing contradiction strictly blocks alert emission."""
    story = Story(
        id="story-alt-conflict",
        title="Disputed Announcement",
        formation_score=80.0,
        contradiction_status="PREDICTION_BLOCKED",
        prediction_eligible=False,
    )
    pred = Prediction(story_id=story.id, formation_probability=0.0, impact_score=0.80, prediction_status="BLOCKED")
    chain = EvidenceChain(story_id=story.id, chain_status="COMPLETE", confidence_score=0.80, items=[])
    db_session.add_all([story, pred, chain])
    await db_session.flush()

    alert = await AlertOrchestratorService.evaluate_and_create_alert(
        db=db_session,
        story=story,
        prediction=pred,
        evidence_chain=chain,
        articles=[],
    )

    assert alert.status == "BLOCKED"
    assert "Load-bearing contradiction detected" in alert.ranking_explanation


@pytest.mark.asyncio
async def test_alert_feedback_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test 5: Analyst feedback on alerts."""
    story = Story(id="story-alt-fb", title="Story FB", status="EMERGING")
    alert = Alert(
        id="alert-fb-01",
        story_id=story.id,
        title="Alert FB",
        headline_in_progress="Alert FB",
        why_it_matters="Matters",
        status="ACTIVE",
    )
    db_session.add_all([story, alert])
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/alerts/{alert.id}/feedback",
        json={"rating": "THUMBS_UP", "notes": "Accurate early signal verification."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_positive"] is True
    assert data["alert_id"] == alert.id
