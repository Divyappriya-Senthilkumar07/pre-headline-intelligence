import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles
from app.services.copilot_service import GroundedCopilotService
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_grounded_copilot_answers_with_citations(db_session: AsyncSession):
    """Test 1: Grounded questions receive answers backed by citations from story evidence."""
    src = Source(id="src-cop-01", name="The Hindu", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add(src)
    await db_session.flush()

    art = Article(
        id="art-cop-01",
        source_id=src.id,
        title="State Pollution Control Board initiates plant inspection at Company X",
        url="https://thehindu.com/probe",
        published_at=datetime.now(timezone.utc),
        language="en",
        excerpt="Officials conducted a surprise compliance check at the manufacturing unit.",
        attribution_text="The Hindu",
    )
    story = Story(
        id="story-cop-01",
        title="Company X Environmental Inspection",
        formation_score=84.0,
        formation_status="CORROBORATED",
        independent_sources_count=2,
        status="EMERGING",
        contradiction_status="CLEAR",
    )
    db_session.add_all([art, story])
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art.id))
    await db_session.commit()

    resp = await GroundedCopilotService.query_copilot(
        db=db_session,
        story_id=story.id,
        question="Why did this story receive a high formation score?",
    )

    assert resp.is_refusal is False
    assert "Formation Score of 84/100" in resp.answer or "84" in resp.answer
    assert len(resp.citations) >= 1
    assert resp.citations[0].source_name == "The Hindu"


@pytest.mark.asyncio
async def test_copilot_strictly_refuses_ungrounded_questions(db_session: AsyncSession):
    """Test 2: Ungrounded external questions (stock prices, outside news) are refused."""
    story = Story(
        id="story-cop-refuse",
        title="Regional Industrial Audit",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.commit()

    resp = await GroundedCopilotService.query_copilot(
        db=db_session,
        story_id=story.id,
        question="What happened to Company X's stock price yesterday?",
    )

    assert resp.is_refusal is True
    assert "I cannot answer that from the available evidence for this story." in resp.answer
    assert resp.evidence_used_count == 0


@pytest.mark.asyncio
async def test_copilot_story_isolation_security(db_session: AsyncSession):
    """Test 3: Copilot query on Story A cannot access or leak Story B's evidence."""
    src_b = Source(id="src-b-priv", name="Confidential Source B", domain="priv.org", source_type="REGIONAL_MEDIA", primary_language="en")
    art_b = Article(id="art-b-priv", source_id=src_b.id, title="Top Secret Probe B", url="https://priv.org/b", published_at=datetime.now(timezone.utc), language="en", excerpt="Secret B details", attribution_text="Confidential Source B")
    
    story_a = Story(id="story-a-iso", title="Story A Public Audit", status="EMERGING")
    story_b = Story(id="story-b-iso", title="Story B Private Probe", status="EMERGING")
    db_session.add_all([src_b, art_b, story_a, story_b])
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story_b.id, article_id=art_b.id))
    await db_session.commit()

    # Query Copilot for Story A asking about Story B details
    resp_a = await GroundedCopilotService.query_copilot(
        db=db_session,
        story_id=story_a.id,
        question="What evidence exists?",
    )

    # Story A response MUST NOT contain Confidential Source B
    assert "Confidential Source B" not in resp_a.answer
    assert all(c.source_name != "Confidential Source B" for c in resp_a.citations)


@pytest.mark.asyncio
async def test_copilot_api_endpoint_and_caching(client: AsyncClient, db_session: AsyncSession):
    """Test 4 & 5: HTTP Copilot API endpoint with response caching."""
    story = Story(id="story-cop-api", title="Factory Compliance Review", status="EMERGING", formation_score=78.0)
    db_session.add(story)
    await db_session.commit()

    # First request -> cache miss
    resp1 = await client.post(
        "/api/v1/copilot/query",
        json={"story_id": story.id, "question": "Why did this story receive this score?"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["cached"] is False
    assert "Factory Compliance Review" in data1["answer"] or "78" in data1["answer"]

    # Second identical request -> cache hit
    resp2 = await client.post(
        "/api/v1/copilot/query",
        json={"story_id": story.id, "question": "Why did this story receive this score?"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["cached"] is True
    assert data2["answer"] == data1["answer"]
