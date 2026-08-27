import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles
from app.models.claim import Claim
from app.models.evidence import EvidenceChain
from app.services.evidence_service import EvidenceService
from app.agents.evidence import EvidenceInvestigationAgent
from app.schemas.agent import EvidenceInvestigationInput


@pytest.mark.asyncio
async def test_evidence_chain_assembly_and_structure(db_session: AsyncSession):
    """Test 1 & 2: Structured Evidence Chain assembly with Source -> Claim -> Evidence -> Corroboration -> Confidence."""
    src = Source(id="src-ev-01", name="State Gazette Desk", domain="gazette.tn.gov.in", source_type="GOVERNMENT", primary_language="ta")
    db_session.add(src)
    await db_session.flush()

    art = Article(
        id="art-ev-01",
        source_id=src.id,
        title="Official Notification: Environmental compliance audit ordered",
        url="https://gazette.tn.gov.in/notifications/2026-audit",
        published_at=datetime.now(timezone.utc),
        language="ta",
        excerpt="The Tamil Nadu State Pollution Control Board has ordered an immediate audit of chemical emissions.",
        attribution_text="State Gazette Desk",
    )
    db_session.add(art)
    await db_session.flush()

    claim = Claim(
        id="claim-ev-01",
        article_id=art.id,
        statement="Tamil Nadu State Pollution Control Board ordered an audit of chemical emissions.",
        claim_type="REGULATORY_ACTION",
        is_load_bearing=True,
    )
    db_session.add(claim)
    await db_session.flush()

    story = Story(id="story-ev-01", title="State Chemical Emissions Audit", status="EMERGING")
    db_session.add(story)
    await db_session.flush()

    # Build Evidence Chain
    chain_res = await EvidenceService.build_evidence_chain(
        db=db_session,
        story=story,
        articles=[art],
        claims=[claim],
    )

    assert chain_res.chain_status in ["COMPLETE", "PARTIAL"]
    assert chain_res.has_sufficient_evidence is True
    assert chain_res.items_count == 1

    item = chain_res.items[0]
    assert item.source_name == "State Gazette Desk"
    assert item.claim_statement == claim.statement
    assert item.evidence_type == "GOVERNMENT_SOURCE"
    # Excerpt should be short and attributed
    assert item.evidence_excerpt.startswith("[State Gazette Desk]:")
    assert len(item.evidence_excerpt) <= 250


@pytest.mark.asyncio
async def test_missing_evidence_sets_insufficient_status(db_session: AsyncSession):
    """Test 4 & 6: Missing evidence triggers INSUFFICIENT_EVIDENCE and prevents alert generation."""
    story = Story(id="story-ev-empty", title="Ghost Story Without Articles", status="EMERGING")
    db_session.add(story)
    await db_session.flush()

    chain_res = await EvidenceService.build_evidence_chain(
        db=db_session,
        story=story,
        articles=[],
    )

    assert chain_res.chain_status == "INSUFFICIENT_EVIDENCE"
    assert chain_res.has_sufficient_evidence is False
    assert chain_res.items_count == 0


@pytest.mark.asyncio
async def test_agent8_evidence_investigation_execution(db_session: AsyncSession):
    """Test 5: Agent 8 EvidenceInvestigationAgent execution."""
    src = Source(id="src-ag8", name="Regional Wire", domain="wire.in", source_type="REGIONAL_MEDIA", primary_language="en")
    art = Article(id="art-ag8", source_id=src.id, title="Probe", url="https://wire.in/p", published_at=datetime.now(timezone.utc), language="en", excerpt="Audit notice", attribution_text="Regional Wire")
    story = Story(id="story-ag8-01", title="Probe", status="EMERGING")
    db_session.add_all([src, art, story])
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art.id))
    await db_session.commit()

    agent = EvidenceInvestigationAgent()
    input_data = EvidenceInvestigationInput(story_id=story.id, query_text="What evidence exists?")
    output = await agent.process(input_data, db=db_session)

    assert len(output.evidence_chain) >= 1
    assert output.traceability_status in ["VERIFIED_AUDITABLE", "INSUFFICIENT_EVIDENCE"]
    assert output.copilot_answer is not None
