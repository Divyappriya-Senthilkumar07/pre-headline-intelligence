import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles


@pytest.mark.asyncio
async def test_story_notes_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """Test 1: Analyst note creation, retrieval, and deletion on a story."""
    story = Story(id="story-note-01", title="Plant Inspection Lead", status="EMERGING")
    db_session.add(story)
    await db_session.commit()

    # Create Note
    resp = await client.post(
        f"/api/v1/stories/{story.id}/notes",
        json={"note": "Verified with regional registry: inspection order #TN-2026 is authentic."},
    )
    assert resp.status_code == 201
    note_data = resp.json()
    assert note_data["story_id"] == story.id
    assert "authentic" in note_data["note"]

    # List Notes
    list_resp = await client.get(f"/api/v1/stories/{story.id}/notes")
    assert list_resp.status_code == 200
    notes = list_resp.json()
    assert len(notes) >= 1
    assert notes[0]["id"] == note_data["id"]

    # Delete Note
    del_resp = await client.delete(f"/api/v1/stories/{story.id}/notes/{note_data['id']}")
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_story_status_actions(client: AsyncClient, db_session: AsyncSession):
    """Test 2: Analyst updates story investigation status."""
    story = Story(id="story-act-01", title="Corporate Governance Probe", status="EMERGING")
    db_session.add(story)
    await db_session.commit()

    # Transition to INVESTIGATING
    resp1 = await client.post(f"/api/v1/stories/{story.id}/status", json={"status": "INVESTIGATING"})
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "INVESTIGATING"

    # Transition to ACKNOWLEDGED
    resp2 = await client.post(f"/api/v1/stories/{story.id}/status", json={"status": "ACKNOWLEDGED"})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ACKNOWLEDGED"


@pytest.mark.asyncio
async def test_story_timeline_retrieval(client: AsyncClient, db_session: AsyncSession):
    """Test 3: Chronological timeline retrieval with source attribution."""
    src = Source(id="src-time-01", name="Dinamalar Regional", domain="dinamalar.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    art = Article(
        id="art-time-01",
        source_id=src.id,
        title="Inspection Team Arrives",
        url="https://dinamalar.com/t1",
        published_at=datetime.now(timezone.utc),
        language="ta",
        excerpt="Officials arrived at 08:00 AM.",
        attribution_text="Dinamalar Regional",
        is_original_reporting=True,
    )
    story = Story(id="story-time-01", title="Plant Inspection Lead", status="EMERGING")
    db_session.add_all([src, art, story])
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art.id))
    await db_session.commit()

    resp = await client.get(f"/api/v1/stories/{story.id}/timeline")
    assert resp.status_code == 200
    timeline = resp.json()
    assert len(timeline) >= 1
    assert timeline[0]["source_name"] == "Dinamalar Regional"
    assert timeline[0]["event_type"] == "PRIMARY_SIGNAL"
