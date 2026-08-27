import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    User,
    Watchlist,
    Source,
    SourceProfile,
    Article,
    Entity,
    Event,
    GraphEdge,
    Claim,
    Story,
    EvidenceChain,
    Contradiction,
    Prediction,
    Alert,
    Feedback,
)


@pytest.mark.asyncio
async def test_core_models_instantiation_and_persistence(db_session: AsyncSession):
    """Verify that all core database entities can be created and persisted."""
    # 1. User
    user = User(
        email="analyst@pre-headline.ai",
        hashed_password="secure_hash_example",
        full_name="Lead Analyst",
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None

    # 2. Watchlist
    watchlist = Watchlist(
        user_id=user.id,
        name="Key Defense & Regulatory Entities",
        entities=["Company X", "Department of Regulatory Affairs"],
        keywords=["inspection", "compliance", "notice"],
        languages=["ta", "hi", "en"],
    )
    db_session.add(watchlist)
    await db_session.flush()
    assert watchlist.id is not None

    # 3. Source & SourceProfile
    source = Source(
        name="Tamil Nadu Regional Daily",
        domain="dinamalar.com",
        source_type="REGIONAL_MEDIA",
        country="India",
        region="Tamil Nadu",
        primary_language="ta",
    )
    db_session.add(source)
    await db_session.flush()

    source_profile = SourceProfile(
        source_id=source.id,
        independence_score=0.92,
        syndication_links=[],
        reliability_score=0.88,
    )
    db_session.add(source_profile)
    await db_session.flush()

    # 4. Article (Legal excerpt only + vector embedding)
    article = Article(
        source_id=source.id,
        title="State inspection team visits manufacturing plant",
        url="https://dinamalar.com/news/state-inspection-101",
        published_at=datetime.utcnow(),
        language="ta",
        excerpt="Officials conducted an inspection regarding environmental compliance standards.",
        attribution_text="Source: Dinamalar (Tamil Nadu Regional)",
        embedding=[0.01] * 384,
        is_original_reporting=True,
    )
    db_session.add(article)
    await db_session.flush()
    assert article.id is not None

    # 5. Entity & Event
    entity = Entity(
        name="Company X",
        entity_type="COMPANY",
        canonical_name="Company X Global Ltd.",
        aliases=["Company X", "Comp-X"],
    )
    event = Event(
        title="Facility Environmental Inspection",
        event_type="REGULATORY_INSPECTION",
        location="Tamil Nadu",
    )
    db_session.add_all([entity, event])
    await db_session.flush()

    # 6. GraphEdge (PostgreSQL Adjacency List)
    edge = GraphEdge(
        source_node_id=source.id,
        source_type="SOURCE",
        target_node_id=event.id,
        target_type="EVENT",
        edge_type="reported",
        properties={"corroboration_level": "direct_witness"},
    )
    db_session.add(edge)
    await db_session.flush()

    # 7. Claim (with is_load_bearing flag)
    claim1 = Claim(
        article_id=article.id,
        statement="State environmental enforcement teams initiated a formal site probe.",
        claim_type="FACT",
        is_load_bearing=True,
        confidence=0.95,
        language="ta",
        embedding=[0.02] * 384,
    )
    claim2 = Claim(
        article_id=article.id,
        statement="Company leadership confirmed routine review schedule.",
        claim_type="OFFICIAL_STATEMENT",
        is_load_bearing=True,
        confidence=0.85,
        language="ta",
        embedding=[0.03] * 384,
    )
    db_session.add_all([claim1, claim2])
    await db_session.flush()

    # 8. Story & Join Tables
    story = Story(
        title="Company X Regulatory Inspection Probe",
        why_it_matters="Independent multi-lingual regional reporting indicates unannounced regulatory review.",
        formation_score=0.88,
        independent_sources_count=3,
        languages=["ta", "hi", "en"],
    )
    story.articles.append(article)
    story.entities.append(entity)
    db_session.add(story)
    await db_session.flush()
    assert story.id is not None

    # 9. EvidenceChain
    evidence = EvidenceChain(
        story_id=story.id,
        claim_id=claim1.id,
        source_id=source.id,
        step_order=1,
        evidence_type="OFFICIAL_DOCUMENT",
        claim_text=claim1.statement,
        supporting_quote="Inspection notice ref #TN-ENV-2026-88.",
        corroborating_sources_count=3,
        confidence_score=0.92,
    )
    db_session.add(evidence)
    await db_session.flush()

    # 10. Contradiction
    contradiction = Contradiction(
        story_id=story.id,
        claim_a_id=claim1.id,
        claim_b_id=claim2.id,
        is_load_bearing=True,
        status="UNRESOLVED",
        severity="CRITICAL",
        description="Conflict between official enforcement inspection and company routine maintenance claim.",
        halted_prediction=True,
    )
    db_session.add(contradiction)
    await db_session.flush()

    # 11. Prediction
    prediction = Prediction(
        story_id=story.id,
        formation_score=0.88,
        probability=0.85,
        impact=0.88,
        trajectory_stage="REGIONAL",
        is_halted=True,
        halt_reason="Contradiction Gate: Load-bearing conflict active.",
    )
    db_session.add(prediction)
    await db_session.flush()

    # 12. Alert & Feedback
    alert = Alert(
        story_id=story.id,
        title="Emerging Intelligence: Company X Regulatory Inspection",
        why_it_matters="Multi-lingual corroboration across 3 sources.",
        urgency=0.90,
        probability=0.85,
        impact=0.88,
        rank_score=0.673,
        formation_confidence="HIGH",
        independent_sources_count=3,
        languages=["ta", "hi", "en"],
    )
    db_session.add(alert)
    await db_session.flush()

    feedback = Feedback(
        alert_id=alert.id,
        user_id=user.id,
        is_positive=True,
        score=1,
        feedback_type="ACCURATE_FORMATION",
        notes="High quality early detection before English national pickup.",
    )
    db_session.add(feedback)
    await db_session.commit()

    # Verify query
    res = await db_session.execute(select(Story).where(Story.id == story.id))
    fetched_story = res.scalars().first()
    assert fetched_story is not None
    assert fetched_story.formation_score == 0.88
    assert len(fetched_story.articles) == 1
    assert len(fetched_story.entities) == 1
