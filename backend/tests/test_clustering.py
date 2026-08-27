import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.source import Source
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity
from app.services.clustering_service import StoryClusteringService
from app.services.embedding_service import MultilingualEmbeddingService
from app.services.graph_service import GraphService


@pytest.mark.asyncio
async def test_cross_language_hdbscan_clustering(db_session: AsyncSession):
    """Test 12, 13, 14, 15, 16, 17: Cross-language HDBSCAN clustering, noise handling, and Story creation."""
    # 1. Setup Sources
    source = Source(id="src-clust-01", name="Global Wire", domain="global.org", source_type="RSS_FEED", primary_language="en")
    db_session.add(source)
    await db_session.flush()

    embedder = MultilingualEmbeddingService()
    now = datetime.now(timezone.utc)

    # 2. Setup 3 cross-lingual articles discussing the SAME event (Company X inspection)
    art_en = Article(
        id="art-cl-en",
        source_id=source.id,
        title="State Pollution Control Board inspects Company X manufacturing plant",
        url="https://global.org/en/inspection",
        published_at=now,
        language="en",
        excerpt="Officials conducted a surprise compliance audit at Company X industrial unit.",
        attribution_text="Source: Global Wire",
    )
    art_en.embedding = embedder.embed_text(f"{art_en.title} {art_en.excerpt}")

    art_ta = Article(
        id="art-cl-ta",
        source_id=source.id,
        title="கம்பெனி எக்ஸ் தொழிற்சாலையில் அதிகாரிகள் ஆய்வு மேற்கொண்டனர்",
        url="https://global.org/ta/inspection",
        published_at=now,
        language="ta",
        excerpt="தமிழக அரசு அதிகாரிகள் தீவிர ஆய்வு நடத்தினர்.",
        attribution_text="Source: Global Wire",
    )
    art_ta.embedding = embedder.embed_text(f"{art_ta.title} {art_ta.excerpt}")

    art_hi = Article(
        id="art-cl-hi",
        source_id=source.id,
        title="कंपनी एक्स संयंत्र में प्रदूषण नियंत्रण बोर्ड द्वारा निरीक्षण",
        url="https://global.org/hi/inspection",
        published_at=now,
        language="hi",
        excerpt="अधिकारियों ने संयंत्र में सुरक्षा और अनुपालन की जांच की।",
        attribution_text="Source: Global Wire",
    )
    art_hi.embedding = embedder.embed_text(f"{art_hi.title} {art_hi.excerpt}")

    # 3. Setup 1 outlier/noise article (cricket match)
    art_noise = Article(
        id="art-cl-noise",
        source_id=source.id,
        title="Local tournament finals conclude in southern district",
        url="https://global.org/sports/cricket",
        published_at=now,
        language="en",
        excerpt="Championship trophy awarded following cricket match victory.",
        attribution_text="Source: Global Wire",
    )
    art_noise.embedding = embedder.embed_text(f"{art_noise.title} {art_noise.excerpt}")

    db_session.add_all([art_en, art_ta, art_hi, art_noise])
    await db_session.flush()

    # Create entity & connect to cluster articles
    comp_x = await GraphService.upsert_entity(db_session, "Company X", "COMPANY")
    await GraphService.add_edge(db_session, art_en.id, comp_x.id, "mentions")
    await GraphService.add_edge(db_session, art_ta.id, comp_x.id, "mentions")
    await GraphService.add_edge(db_session, art_hi.id, comp_x.id, "mentions")
    await db_session.commit()

    # 4. Execute Clustering
    all_articles = [art_en, art_ta, art_hi, art_noise]
    stories = await StoryClusteringService.cluster_articles(
        db=db_session,
        articles=all_articles,
        min_cluster_size=2,
    )

    # Must produce 1 Story cluster
    assert len(stories) == 1
    story = stories[0]
    assert story.status == "EMERGING"

    # Verify story_articles join table (must contain 3 related articles, NOT the noise article)
    res_art = await db_session.execute(
        select(story_articles.c.article_id).where(story_articles.c.story_id == story.id)
    )
    linked_art_ids = res_art.scalars().all()
    assert len(linked_art_ids) == 3
    assert art_noise.id not in linked_art_ids
    assert art_en.id in linked_art_ids
    assert art_ta.id in linked_art_ids
    assert art_hi.id in linked_art_ids

    # Verify story_entities join table
    res_ent = await db_session.execute(
        select(story_entities.c.entity_id).where(story_entities.c.story_id == story.id)
    )
    linked_ent_ids = res_ent.scalars().all()
    assert comp_x.id in linked_ent_ids

    # Verify multilingual representation in metadata
    meta = story.metadata_json
    assert "en" in meta["languages"]
    assert "ta" in meta["languages"]
    assert "hi" in meta["languages"]
