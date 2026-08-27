import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.graph import Entity, Event, GraphEdge
from app.models.article import Article
from app.models.source import Source
from app.services.graph_service import GraphService
from app.agents.expansion import ExpansionAgent
from app.schemas.agent import ExpansionInput, EnrichedArticle


@pytest.mark.asyncio
async def test_graph_node_upsert_and_deduplication(db_session: AsyncSession):
    """Test 5 & 7: Graph node creation and duplicate prevention."""
    e1 = await GraphService.upsert_entity(
        db=db_session,
        canonical_name="Company X Pvt Ltd",
        entity_type="COMPANY",
        raw_mention="Company X Pvt Ltd",
    )
    assert e1.canonical_name == "Company X"

    e2 = await GraphService.upsert_entity(
        db=db_session,
        canonical_name="Company X",
        entity_type="COMPANY",
        raw_mention="company-x",
    )
    assert e1.id == e2.id

    res = await db_session.execute(select(Entity).where(Entity.canonical_name == "Company X"))
    ents = res.scalars().all()
    assert len(ents) == 1
    assert "company-x" in ents[0].aliases


@pytest.mark.asyncio
async def test_graph_edge_creation_and_bounded_expansion(db_session: AsyncSession):
    """Test 6 & 8: Graph edge creation and Agent 3 bounded expansion."""
    source = Source(id="src-exp-01", name="Regional Wire", domain="wire.org", source_type="RSS_FEED", primary_language="en")
    db_session.add(source)
    await db_session.flush()

    art1 = Article(
        id="art-exp-01",
        source_id=source.id,
        title="Inspection at Company X",
        url="https://wire.org/01",
        published_at=datetime.now(timezone.utc),
        language="en",
        excerpt="Inspection occurred",
        attribution_text="Source: Regional Wire",
    )
    art2 = Article(
        id="art-exp-02",
        source_id=source.id,
        title="ஆய்வு அறிக்கை",
        url="https://wire.org/02",
        published_at=datetime.now(timezone.utc),
        language="ta",
        excerpt="அரசு அறிக்கை",
        attribution_text="Source: Regional Wire",
    )
    db_session.add_all([art1, art2])
    await db_session.flush()

    comp_x = await GraphService.upsert_entity(db_session, "Company X", "COMPANY")
    regulator = await GraphService.upsert_entity(db_session, "TNSPCB", "REGULATOR")

    await GraphService.add_edge(db_session, art1.id, comp_x.id, "mentions", source_type="ARTICLE", target_type="ENTITY")
    await GraphService.add_edge(db_session, art2.id, comp_x.id, "mentions", source_type="ARTICLE", target_type="ENTITY")
    await GraphService.add_edge(db_session, comp_x.id, regulator.id, "investigated_by", source_type="ENTITY", target_type="ENTITY")
    await db_session.commit()

    agent = ExpansionAgent()
    input_data = ExpansionInput(
        enriched_articles=[
            EnrichedArticle(
                article_id=art1.id,
                title=art1.title,
                url=art1.url,
                language=art1.language,
                is_relevant=True,
                relevance_score=0.90,
                extracted_entities=[],
                extracted_events=[],
                summary=art1.excerpt,
            )
        ],
        max_depth=2,
        max_results=10,
    )

    output = await agent.process(input_data, db=db_session)
    assert output.status == "success"
    assert output.expansion_edges_count >= 2
    assert any(a.url == art2.url for a in output.expanded_articles)
    assert "ta" in output.languages_represented
