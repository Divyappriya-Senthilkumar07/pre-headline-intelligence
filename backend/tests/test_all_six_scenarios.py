import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.replay_engine import ReplayEngine


@pytest.mark.asyncio
async def test_scenario_1_successful_early_detection(client: AsyncClient, db_session: AsyncSession):
    """Scenario 1: Story forms from local Tamil to national headline with 2.5h lead time."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-1-early-detection/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "EARLY_DETECTION"
    assert res["first_valid_alert_time"] is not None
    assert res["lead_time_status"] == "DETECTED_EARLY"
    assert res["lead_time_hours"] == 2.5  # 11:40 AM minus 09:10 AM = 2.5 hours (150 min)


@pytest.mark.asyncio
async def test_scenario_2_syndication_trap(client: AsyncClient, db_session: AsyncSession):
    """Scenario 2: Wire copies do not inflate independent source count; alert is suppressed."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-2-syndication-trap/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "SYNDICATION_TRAP"
    # Even after 4 articles, independent sources remains 1
    last_step = res["timeline"][-1]
    assert last_step["total_articles"] == 4
    assert last_step["independent_sources"] == 1
    assert last_step["formation_score"] < 45.0
    assert res["first_valid_alert_time"] is None  # No false alert


@pytest.mark.asyncio
async def test_scenario_3_multilingual_convergence(client: AsyncClient, db_session: AsyncSession):
    """Scenario 3: Multi-Indic coverage converges and fires early alert."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-3-multilingual-convergence/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "MULTILINGUAL_CONVERGENCE"
    last_step = res["timeline"][-1]
    assert last_step["independent_sources"] == 3
    assert last_step["formation_score"] >= 85.0
    assert res["first_valid_alert_time"] is not None
    assert res["lead_time_status"] == "DETECTED_EARLY"


@pytest.mark.asyncio
async def test_scenario_4_contradiction_gate_blocking(client: AsyncClient, db_session: AsyncSession):
    """Scenario 4: Conflicting load-bearing claims halt prediction and block alert."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-4-contradiction/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "CONTRADICTION"
    last_step = res["timeline"][-1]
    assert last_step["contradiction_status"] == "PREDICTION_BLOCKED"
    assert last_step["is_prediction_blocked"] is True
    assert last_step["probability"] == 0.0
    assert res["first_valid_alert_time"] is None  # Alert strictly blocked


@pytest.mark.asyncio
async def test_scenario_5_false_signal(client: AsyncClient, db_session: AsyncSession):
    """Scenario 5: Uncorroborated fringe rumor does not progress to target milestone."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-5-false-signal/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "FALSE_SIGNAL"
    assert res["lead_time_status"] == "NOT_APPLICABLE"
    assert res["first_valid_alert_time"] is None


@pytest.mark.asyncio
async def test_scenario_6_missed_story(client: AsyncClient, db_session: AsyncSession):
    """Scenario 6: Sudden breaking news with no prior signal correctly identified as missed story."""
    resp = await client.post("/api/v1/replay/scenarios/scenario-6-missed-story/run")
    assert resp.status_code == 200
    res = resp.json()

    assert res["scenario_type"] == "MISSED_STORY"
    assert res["first_valid_alert_time"] is None
    assert res["lead_time_status"] == "NOT_DETECTED"
