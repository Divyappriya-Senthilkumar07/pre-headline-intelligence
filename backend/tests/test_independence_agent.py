import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles
from app.models.graph import Entity
from app.services.independence_service import IndependenceService
from app.agents.independence import IndependenceAgent
from app.schemas.agent import IndependenceInput


@pytest.mark.asyncio
async def test_single_source_and_same_publisher_derivative_handling(db_session: AsyncSession):
    """Test 1 & 2: Single source and multiple articles from the same publisher network."""
    # Create 1 Source
    src = Source(
        id="src-pub-01",
        name="Daily Press Network",
        domain="dailypress.org",
        source_type="REGIONAL_MEDIA",
        primary_language="en",
    )
    db_session.add(src)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    art1 = Article(
        id="art-same-01",
        source_id=src.id,
        title="Company X industrial plant inspection initiated by state board",
        url="https://dailypress.org/news/company-x-probe",
        published_at=now,
        language="en",
        excerpt="Officials initiated an environmental audit at the factory premises.",
        attribution_text="Daily Press Network",
    )
    art2 = Article(
        id="art-same-02",
        source_id=src.id,
        title="Follow-up: Company X factory inspection update",
        url="https://dailypress.org/updates/company-x-probe",
        published_at=now + timedelta(minutes=20),
        language="en",
        excerpt="Additional team members joined the ongoing plant inspection.",
        attribution_text="Daily Press Network",
    )
    db_session.add_all([art1, art2])
    await db_session.flush()

    # Analyze Independence
    res = await IndependenceService.analyze_story_independence(
        db=db_session,
        story_id="story-same-pub",
        articles=[art1, art2],
    )

    # 2 articles from same publisher MUST yield only 1 independent source
    assert res.total_articles_count == 2
    assert res.independent_sources_count == 1
    assert res.source_relationships[0].relationship_type in ["ORIGINAL", "INDEPENDENT"]
    assert res.source_relationships[1].relationship_type in ["RELATED", "COPIED"]


@pytest.mark.asyncio
async def test_syndication_and_rapid_copy_detection(db_session: AsyncSession):
    """Test 3 & 8: Simultaneous wire copies are detected as SYNDICATED/COPIED with low temporal spread."""
    src1 = Source(id="src-wire-01", name="PTI Wire", domain="pti.in", source_type="WIRE_SERVICE", primary_language="en")
    src2 = Source(id="src-copy-02", name="Aggregator Daily", domain="aggregator.com", source_type="REGIONAL_MEDIA", primary_language="en")
    src3 = Source(id="src-copy-03", name="Local Flash", domain="localflash.net", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src1, src2, src3])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Lead wire story
    art1 = Article(
        id="art-wire-01",
        source_id=src1.id,
        title="State Pollution Control Board inspects Company X manufacturing plant",
        url="https://pti.in/wire/company-x-inspection",
        published_at=now,
        language="en",
        excerpt="PTI Wire: State Pollution Control Board conducted surprise inspection at Company X unit.",
        attribution_text="PTI Wire",
    )
    # Copied 1 minute later with identical excerpt
    art2 = Article(
        id="art-copy-02",
        source_id=src2.id,
        title="State Pollution Control Board inspects Company X manufacturing plant",
        url="https://aggregator.com/news/company-x",
        published_at=now + timedelta(minutes=1),
        language="en",
        excerpt="PTI Wire: State Pollution Control Board conducted surprise inspection at Company X unit.",
        attribution_text="Aggregator Daily",
    )
    # Copied 2 minutes later
    art3 = Article(
        id="art-copy-03",
        source_id=src3.id,
        title="State Pollution Control Board inspects Company X manufacturing plant",
        url="https://localflash.net/feed/company-x",
        published_at=now + timedelta(minutes=2),
        language="en",
        excerpt="State Pollution Control Board conducted surprise inspection at Company X unit.",
        attribution_text="Local Flash",
    )
    db_session.add_all([art1, art2, art3])
    await db_session.flush()

    res = await IndependenceService.analyze_story_independence(
        db=db_session,
        story_id="story-wire-syndicate",
        articles=[art1, art2, art3],
    )

    assert res.total_articles_count == 3
    # Despite 3 articles, independent sources count should be 1
    assert res.independent_sources_count == 1
    assert res.source_relationships[1].relationship_type in ["SYNDICATED", "COPIED"]
    assert res.source_relationships[2].relationship_type in ["SYNDICATED", "COPIED"]
    # Temporal spread score penalized for simultaneous syndication blast
    assert res.temporal_spread_score <= 0.40


@pytest.mark.asyncio
async def test_genuinely_independent_cross_lingual_sources(db_session: AsyncSession):
    """Test 4 & 5: Genuinely independent publishers across English, Tamil, and Hindi."""
    src_en = Source(id="src-ind-en", name="The Hindu", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    src_ta = Source(id="src-ind-ta", name="Dinamani", domain="dinamani.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src_hi = Source(id="src-ind-hi", name="Dainik Bhaskar", domain="bhaskar.com", source_type="REGIONAL_MEDIA", primary_language="hi")
    db_session.add_all([src_en, src_ta, src_hi])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    art_en = Article(
        id="art-ind-en",
        source_id=src_en.id,
        title="State Pollution Control Board conducts scheduled audit of Company X plant",
        url="https://thehindu.com/news/national/tamil-nadu/company-x-inspection",
        published_at=now,
        language="en",
        excerpt="Officials initiated comprehensive compliance audit of chemical discharge at Chennai unit.",
        attribution_text="The Hindu",
    )
    art_ta = Article(
        id="art-ind-ta",
        source_id=src_ta.id,
        title="கம்பெனி எக்ஸ் தொழிற்கூடத்தில் அதிகாரிகள் ஆய்வு",
        url="https://dinamani.com/tamilnadu/company-x-audit",
        published_at=now + timedelta(minutes=45),
        language="ta",
        excerpt="தமிழக அரசு மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு மேற்கொண்டனர்.",
        attribution_text="Dinamani",
    )
    art_hi = Article(
        id="art-ind-hi",
        source_id=src_hi.id,
        title="कंपनी एक्स संयंत्र में प्रदूषण नियंत्रण बोर्ड का औचक दौरा",
        url="https://bhaskar.com/business/company-x-probe",
        published_at=now + timedelta(hours=2),
        language="hi",
        excerpt="प्रदूषण नियंत्रण बोर्ड के वरिष्ठ अधिकारियों ने पर्यावरण सुरक्षा मानकों की समीक्षा की।",
        attribution_text="Dainik Bhaskar",
    )
    db_session.add_all([art_en, art_ta, art_hi])
    await db_session.flush()

    story = Story(
        id="story-ind-cross-lingual",
        title="State Environmental Audit at Company X Facilities",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.flush()

    agent = IndependenceAgent()
    input_data = IndependenceInput(
        story_id=story.id,
        article_ids=[art_en.id, art_ta.id, art_hi.id],
    )

    output = await agent.process(input_data, db=db_session)
    assert output.total_articles_count == 3
    assert output.independent_sources_count == 3
    assert output.source_diversity_score >= 0.70
    assert output.temporal_spread_score >= 0.75
    assert output.independence_score >= 0.75
    assert output.has_load_bearing_contradiction is False
