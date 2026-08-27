import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.evaluation_service import EvaluationService


@pytest.mark.asyncio
async def test_lead_time_and_precision_recall_metrics(client: AsyncClient, db_session: AsyncSession):
    """
    Test lead time math, precision/recall metrics, calibration, cluster purity,
    and failure analysis.
    """
    resp = await client.post("/api/v1/evaluation/run", json={"dataset_version": "v1.0.0"})
    assert resp.status_code == 200
    eval_res = resp.json()

    metrics = eval_res["metrics"]

    # 1. Lead Time assertions
    lead_time = metrics["lead_time"]
    assert lead_time["average_lead_time_hours"] > 1.0
    assert lead_time["count_detected"] >= 2
    assert lead_time["count_missed"] >= 1
    assert lead_time["count_not_applicable"] >= 2
    assert lead_time["sample_size"] == 6

    # 2. Precision & Recall assertions
    pr = metrics["precision_recall"]
    assert pr["precision"] == 1.0  # All fired alerts in seed fixtures were true targets
    assert pr["recall"] >= 0.60  # Detected targets / total targets
    assert pr["total_target_stories"] == 3
    assert pr["true_positives"] == 2

    # 3. Calibration bins assertions
    cal = metrics["calibration_bins"]
    assert len(cal) == 5
    assert any(b["bin"] == "0.8 - 1.0" and b["empirical_success_rate"] == 1.0 for b in cal)

    # 4. Cluster Purity assertions
    purity = metrics["cluster_purity"]
    assert purity["purity_score"] == 1.0

    # 5. Missed Stories analysis
    missed = metrics["missed_stories"]
    assert len(missed) >= 1
    assert missed[0]["scenario_id"] == "scenario-6-missed-story"
    assert "FLASH" in missed[0]["root_cause_failure"] or "INSUFFICIENT" in missed[0]["root_cause_failure"]
