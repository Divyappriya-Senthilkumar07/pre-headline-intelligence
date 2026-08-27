import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.replay_engine import ReplayEngine


@pytest.mark.asyncio
async def test_strict_lookahead_bias_prevention(client: AsyncClient, db_session: AsyncSession):
    """
    MANDATORY EVALUATION TEST:
    Prove that at step 1 (08:00 AM):
    - Total articles == 1
    - Independent sources == 1
    - Languages == ['ta']
    - Formation score is local (< 40.0)
    - Future Hindi and English articles (at 08:45, 09:10, 10:30, 11:40) have ZERO presence or influence.

    At step 3 (08:45 AM):
    - Independent sources == 2
    - Hindi desk (at 09:10) is still completely absent.
    """
    # Execute only step 1
    resp_step1 = await client.post("/api/v1/replay/scenarios/scenario-1-early-detection/run?step=1")
    assert resp_step1.status_code == 200
    data_step1 = resp_step1.json()

    assert data_step1["completed_steps"] == 1
    step1_entry = data_step1["timeline"][0]

    # Look-ahead checks for Step 1
    assert step1_entry["total_articles"] == 1
    assert step1_entry["independent_sources"] == 1
    assert step1_entry["language"] == "ta"
    assert step1_entry["formation_score"] <= 40.0
    assert step1_entry["is_valid_early_alert"] is False
    assert step1_entry["alert_fired"] is False
    assert data_step1["first_valid_alert_time"] is None

    # Execute up to step 3 (08:45 AM)
    resp_step3 = await client.post("/api/v1/replay/scenarios/scenario-1-early-detection/run?step=3")
    assert resp_step3.status_code == 200
    data_step3 = resp_step3.json()

    assert data_step3["completed_steps"] == 3
    step3_entry = data_step3["timeline"][2]

    # Look-ahead checks for Step 3
    assert step3_entry["independent_sources"] == 2
    assert step3_entry["formation_score"] == 68.0
    assert step3_entry["is_valid_early_alert"] is False  # Alert still hasn't fired until 3rd independent desk
    assert data_step3["first_valid_alert_time"] is None
