import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert


@pytest.mark.asyncio
async def test_complete_analyst_workflow_e2e(client: AsyncClient, db_session: AsyncSession):
    """
    End-to-End Complete Analyst Workflow:
    1. Ingestion: Articles arrive from Tamil and English regional desks.
    2. Phase 4 Execution: Generates Prediction, Evidence Chain, and Alerts.
    3. Analyst opens Feed (GET /stories/emerging).
    4. Analyst opens Story Detail (GET /stories/{id}).
    5. Analyst inspects Independence, Formation Score, Timeline (GET /stories/{id}/timeline).
    6. Analyst asks Grounded Copilot (POST /copilot/query).
    7. Analyst adds investigation note (POST /stories/{id}/notes).
    8. Analyst sets story status to INVESTIGATING (POST /stories/{id}/status).
    9. Analyst submits positive feedback on alert (POST /alerts/{id}/feedback).
    """
    # 1. Setup Sources and Articles
    src1 = Source(id="src-p5-1", name="Dinamani Desk", domain="dinamani.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src2 = Source(id="src-p5-2", name="The Hindu Business", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src1, src2])
    await db_session.flush()

    art1 = Article(
        id="art-p5-1",
        source_id=src1.id,
        title="தொழிற்சாலை சுற்றுச்சூழல் ஆய்வு",
        url="https://dinamani.com/audit1",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        language="ta",
        excerpt="அதிகாரிகள் ஆய்வு நடத்தினர்.",
        attribution_text="Dinamani Desk",
        is_original_reporting=True,
    )
    art2 = Article(
        id="art-p5-2",
        source_id=src2.id,
        title="State Pollution Control Board orders compliance review",
        url="https://thehindu.com/audit2",
        published_at=datetime.now(timezone.utc) - timedelta(hours=1),
        language="en",
        excerpt="State Board ordered comprehensive compliance review.",
        attribution_text="The Hindu Business",
        is_original_reporting=True,
    )
    ent = Entity(id="ent-p5-1", name="State Board", canonical_name="State Pollution Board", entity_type="REGULATOR")
    story = Story(
        id="story-p5-e2e",
        title="State Environmental Compliance Review at Industrial Hub",
        why_it_matters="Grounded multi-lingual regional reporting.",
        formation_score=86.0,
        formation_status="CORROBORATED",
        independent_sources_count=2,
        status="EMERGING",
        contradiction_status="CLEAR",
        prediction_eligible=True,
    )
    db_session.add_all([art1, art2, ent, story])
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art1.id))
    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art2.id))
    await db_session.execute(story_entities.insert().values(story_id=story.id, entity_id=ent.id))
    await db_session.commit()

    # 2. Execute Phase 4 Pipeline
    p4_resp = await client.post("/api/v1/pipeline/run-phase4")
    assert p4_resp.status_code == 200

    # 3. Analyst opens Intelligence Feed
    feed_resp = await client.get("/api/v1/stories/emerging")
    assert feed_resp.status_code == 200
    feed_items = feed_resp.json()
    assert len(feed_items) >= 1
    story_alert = next((it for it in feed_items if it["story_id"] == story.id), None)
    assert story_alert is not None
    assert story_alert["status"] == "ACTIVE"

    # 4. Analyst opens Story Detail Workspace
    detail_resp = await client.get(f"/api/v1/stories/{story.id}")
    assert detail_resp.status_code == 200
    story_detail = detail_resp.json()
    assert story_detail["formation_score"] >= 80
    assert story_detail["prediction"] is not None
    assert story_detail["evidence_chain"] is not None

    # 5. Analyst checks Timeline
    timeline_resp = await client.get(f"/api/v1/stories/{story.id}/timeline")
    assert timeline_resp.status_code == 200
    assert len(timeline_resp.json()) == 2

    # 6. Analyst asks Grounded Copilot
    copilot_resp = await client.post(
        "/api/v1/copilot/query",
        json={"story_id": story.id, "question": "Why did this story receive a high formation score?"},
    )
    assert copilot_resp.status_code == 200
    assert copilot_resp.json()["is_refusal"] is False
    assert len(copilot_resp.json()["citations"]) >= 1

    # 7. Analyst adds a persistent investigation note
    note_resp = await client.post(
        f"/api/v1/stories/{story.id}/notes",
        json={"note": "Initial inspection confirmed by regional desk. Awaiting national pickup."},
    )
    assert note_resp.status_code == 201

    # 8. Analyst sets story status to INVESTIGATING
    status_resp = await client.post(
        f"/api/v1/stories/{story.id}/status",
        json={"status": "INVESTIGATING"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "INVESTIGATING"

    # 9. Analyst submits feedback on the alert
    fb_resp = await client.post(
        f"/api/v1/alerts/{story_alert['id']}/feedback",
        json={"rating": "THUMBS_UP", "notes": "Excellent early detection of regional audit signal."},
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["is_positive"] is True
