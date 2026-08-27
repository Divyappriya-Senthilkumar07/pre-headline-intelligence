import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.replay_engine import ReplayEngine


@pytest.mark.asyncio
async def test_replay_scenarios_listing_and_detail(client: AsyncClient, db_session: AsyncSession):
    """Test 1: List all scenarios and retrieve detail with events."""
    await ReplayEngine.seed_scenarios_if_empty(db_session)

    resp = await client.get("/api/v1/replay/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert len(scenarios) == 6

    # Get Scenario 1 detail
    s1_resp = await client.get("/api/v1/replay/scenarios/scenario-1-early-detection")
    assert s1_resp.status_code == 200
    s1_data = s1_resp.json()
    assert s1_data["id"] == "scenario-1-early-detection"
    assert s1_data["events_count"] == 6
    assert len(s1_data["events"]) == 6


@pytest.mark.asyncio
async def test_replay_execution_chronology_and_snapshots(client: AsyncClient, db_session: AsyncSession):
    """Test 2: Chronological execution of Scenario 1 up to step 4."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-1-early-detection/run?step=4")
    assert resp.status_code == 200
    res_data = resp.json()

    assert res_data["total_steps"] == 6
    assert res_data["completed_steps"] == 4
    assert len(res_data["timeline"]) == 4

    # Verify chronological order
    timestamps = [t["timestamp"] for t in res_data["timeline"]]
    assert timestamps == sorted(timestamps)

    # Step 4 should have fired first valid alert
    assert res_data["first_valid_alert_time"] is not None
    assert res_data["first_valid_alert_snapshot"]["independent_sources"] == 3
    assert res_data["first_valid_alert_snapshot"]["formation_score"] >= 80.0
