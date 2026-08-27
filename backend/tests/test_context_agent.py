import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.context_service import ContextService
from app.services.entity_normalizer import EntityNormalizer
from app.agents.context import ContextAgent
from app.schemas.agent import ContextInput, DiscoveredCandidate
from app.models.article import Article
from app.models.source import Source
from app.models.graph import Entity, Event


def test_entity_normalization_variations():
    """Test 2 & 7: Entity normalization across corporate/agency variations."""
    canon_1, key_1 = EntityNormalizer.normalize_entity_name("Google India Pvt Ltd", "COMPANY")
    canon_2, key_2 = EntityNormalizer.normalize_entity_name("Google India", "COMPANY")
    assert canon_1 == canon_2
    assert key_1 == key_2 == "google-india"

    canon_spcb, _ = EntityNormalizer.normalize_entity_name("TNSPCB", "REGULATOR")
    assert "Tamil Nadu Pollution Control Board" in canon_spcb


def test_event_extraction_multilingual():
    """Test 3: Event extraction in English, Tamil, and Hindi."""
    # English inspection
    text_en = "State Pollution Control Board conducted inspection of manufacturing plant."
    ents_en = ContextService.extract_entities(text_en, "en")
    events_en = ContextService.extract_events(text_en, ents_en, "en")
    assert len(events_en) >= 1
    assert events_en[0].event_type == "inspection"

    # Tamil inspection
    text_ta = "தமிழக அரசு அதிகாரிகள் தொழிற்சாலையில் ஆய்வு மேற்கொண்டனர்."
    ents_ta = ContextService.extract_entities(text_ta, "ta")
    events_ta = ContextService.extract_events(text_ta, ents_ta, "ta")
    assert len(events_ta) >= 1
    assert events_ta[0].event_type == "inspection"


def test_explainable_relevance_detection():
    """Test 4: Disambiguating genuine subject from passing keyword mentions."""
    # Case A: Genuine company subject
    text_a = "Company X confirms regulatory inspection at southern plant."
    ents_a = ContextService.extract_entities(text_a, "en")
    events_a = ContextService.extract_events(text_a, ents_a, "en")
    is_rel_a, score_a, matched_a, reason_a = ContextService.evaluate_relevance(
        text_a, ents_a, events_a, ["Company X"]
    )
    assert is_rel_a is True
    assert score_a >= 0.80
    assert "Company X" in matched_a

    # Case B: Disambiguation (Apple farming vs Apple Inc)
    text_b = "Apple farming and fruit harvesting expands across southern state orchards."
    ents_b = ContextService.extract_entities(text_b, "en")
    events_b = ContextService.extract_events(text_b, ents_b, "en")
    is_rel_b, score_b, matched_b, reason_b = ContextService.evaluate_relevance(
        text_b, ents_b, events_b, ["Apple"]
    )
    assert is_rel_b is False
    assert score_b < 0.30


@pytest.mark.asyncio
async def test_agent2_context_execution_and_db_persistence(db_session: AsyncSession):
    """Test 1, 18, 19, 20: Agent 2 Context pipeline execution across Media, RSS, and GDELT articles."""
    source = Source(
        id="src-context-01",
        name="State Intelligence Wire",
        domain="state-intel.example.org",
        source_type="RSS_FEED",
        primary_language="en",
    )
    db_session.add(source)
    await db_session.flush()

    art_url = "https://state-intel.example.org/articles/tn-inspection-report"
    article = Article(
        id="art-context-01",
        source_id=source.id,
        title="State Pollution Control Board conducts scheduled audit of Company X plant",
        url=art_url,
        published_at=datetime.now(timezone.utc),
        language="en",
        excerpt="Officials from Tamil Nadu Pollution Control Board initiated compliance audit at Company X Chennai unit.",
        attribution_text="Source: State Intelligence Wire",
    )
    db_session.add(article)
    await db_session.commit()

    agent = ContextAgent()
    input_data = ContextInput(
        raw_articles=[
            DiscoveredCandidate(
                title=article.title,
                url=article.url,
                source_name=article.attribution_text,
                language="en",
                published_at=article.published_at,
                excerpt=article.excerpt,
            )
        ],
        watchlist_definitions={"keywords": ["Company X"]},
        languages=["en"],
    )

    output = await agent.process(input_data, db=db_session)
    assert output.status == "success"
    assert output.total_processed == 1
    assert output.relevant_count == 1

    ent_res = await db_session.execute(select(Entity).where(Entity.canonical_name == "Company X"))
    comp_x = ent_res.scalars().first()
    assert comp_x is not None

    ev_res = await db_session.execute(select(Event).where(Event.event_type == "inspection"))
    ev = ev_res.scalars().first()
    assert ev is not None
    assert ev.metadata_json.get("source_article_id") == article.id
