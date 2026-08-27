import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.story import Story


@pytest.mark.asyncio
async def test_watchlist_create_list_and_matching_stories(client: AsyncClient, db_session: AsyncSession):
    """Test 1: Watchlist creation and dynamic matching stories calculation."""
    story = Story(
        id="story-wl-01",
        title="State Pollution Board conducts surprise audit at Company X manufacturing plant",
        why_it_matters="Regional compliance audit underway.",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.commit()

    # Create Watchlist
    resp = await client.post(
        "/api/v1/watchlists",
        json={
            "name": "State Environmental Audits",
            "description": "Watchlist for industrial emissions and state inspections",
            "entities": ["Company X", "State Pollution Board"],
            "keywords": ["audit", "inspection", "compliance"],
            "languages": ["ta", "hi", "en"],
        },
    )
    assert resp.status_code == 201
    wl_data = resp.json()
    assert wl_data["name"] == "State Environmental Audits"
    assert wl_data["matching_stories_count"] >= 1

    # List Watchlists
    list_resp = await client.get("/api/v1/watchlists")
    assert list_resp.status_code == 200
    all_wls = list_resp.json()
    assert any(w["id"] == wl_data["id"] for w in all_wls)


@pytest.mark.asyncio
async def test_watchlist_update_toggle_and_delete(client: AsyncClient, db_session: AsyncSession):
    """Test 2: Watchlist update, toggle active status, and deletion."""
    create_resp = await client.post(
        "/api/v1/watchlists",
        json={
            "name": "Initial Watchlist",
            "entities": ["Entity A"],
            "keywords": ["Keyword A"],
        },
    )
    assert create_resp.status_code == 201
    wl_id = create_resp.json()["id"]

    # Update
    put_resp = await client.put(
        f"/api/v1/watchlists/{wl_id}",
        json={"name": "Updated Watchlist Title", "description": "New description"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Updated Watchlist Title"

    # Toggle active
    toggle_resp = await client.post(f"/api/v1/watchlists/{wl_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    # Delete
    del_resp = await client.delete(f"/api/v1/watchlists/{wl_id}")
    assert del_resp.status_code == 204

    # Verify not found
    get_resp = await client.get(f"/api/v1/watchlists/{wl_id}")
    assert get_resp.status_code == 404
