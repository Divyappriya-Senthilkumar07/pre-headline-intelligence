import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Story
from app.models.alert import Alert
from app.models.contradiction import Contradiction


@pytest.mark.asyncio
async def test_alert_status_filtering_and_lifecycle_guard(client: AsyncClient, db_session: AsyncSession):
    """Test 1 & 2: Status filtering and guard preventing unblocking without resolving contradiction."""
    story = Story(id="story-lc-01", title="Dispute on Permit Grant", status="EMERGING", contradiction_status="PREDICTION_BLOCKED")
    contra = Contradiction(
        id="con-lc-01",
        story_id=story.id,
        claim_a_id="cl-1",
        claim_b_id="cl-2",
        is_load_bearing=True,
        status="OPEN",
        severity="CRITICAL",
        description="Contradiction on permit status",
        halted_prediction=True,
    )
    alert = Alert(
        id="alert-lc-01",
        story_id=story.id,
        title="Alert Dispute",
        headline_in_progress="Halted: Permit Dispute",
        why_it_matters="Dispute in progress.",
        contradiction_status="PREDICTION_BLOCKED",
        status="BLOCKED",
    )
    db_session.add_all([story, contra, alert])
    await db_session.commit()

    # Filter by BLOCKED status
    resp_flt = await client.get("/api/v1/alerts?status=BLOCKED")
    assert resp_flt.status_code == 200
    blocked_list = resp_flt.json()
    assert any(a["id"] == alert.id for a in blocked_list)

    # Attempt to transition BLOCKED alert to ACTIVE without resolving contradiction -> must fail with 400
    resp_bad = await client.post(f"/api/v1/alerts/{alert.id}/status", json={"status": "ACTIVE"})
    assert resp_bad.status_code == 400
    assert "Resolve the contradiction first" in resp_bad.json()["detail"]

    # Transition to INVESTIGATING -> allowed
    resp_inv = await client.post(f"/api/v1/alerts/{alert.id}/status", json={"status": "INVESTIGATING"})
    assert resp_inv.status_code == 200
    assert resp_inv.json()["status"] == "INVESTIGATING"


@pytest.mark.asyncio
async def test_resolving_contradiction_enables_alert_activation(client: AsyncClient, db_session: AsyncSession):
    """Test 3: Resolving contradiction unblocks story and enables alert activation."""
    story = Story(id="story-lc-02", title="Disputed Factory Order", status="EMERGING", contradiction_status="PREDICTION_BLOCKED")
    contra = Contradiction(
        id="con-lc-02",
        story_id=story.id,
        claim_a_id="cl-3",
        claim_b_id="cl-4",
        is_load_bearing=True,
        status="UNRESOLVED",
        severity="CRITICAL",
        description="Factory dispute",
        halted_prediction=True,
    )
    alert = Alert(
        id="alert-lc-02",
        story_id=story.id,
        title="Factory Alert",
        why_it_matters="Matters",
        contradiction_status="PREDICTION_BLOCKED",
        status="BLOCKED",
    )
    db_session.add_all([story, contra, alert])
    await db_session.commit()

    # Resolve contradiction via API
    res_resolve = await client.post(
        f"/api/v1/stories/{story.id}/contradictions/{contra.id}/resolve",
        json={"resolution_notes": "Official gazette verified."},
    )
    assert res_resolve.status_code == 200

    # Now activate alert -> allowed
    resp_act = await client.post(f"/api/v1/alerts/{alert.id}/status", json={"status": "ACTIVE"})
    assert resp_act.status_code == 200
    assert resp_act.json()["status"] == "ACTIVE"
