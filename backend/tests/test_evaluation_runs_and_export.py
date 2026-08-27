import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.evaluation_service import EvaluationService


@pytest.mark.asyncio
async def test_evaluation_runs_lifecycle_and_export(client: AsyncClient, db_session: AsyncSession):
    """
    Test running evaluation, listing runs, getting latest, and exporting JSON/CSV.
    """
    # 1. Run evaluation
    run_resp = await client.post("/api/v1/evaluation/run", json={"dataset_version": "v1.0.0"})
    assert run_resp.status_code == 200
    eval_run_id = run_resp.json()["evaluation_run_id"]

    # 2. List runs
    list_resp = await client.get("/api/v1/evaluation/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1
    assert any(r["id"] == eval_run_id for r in runs)

    # 3. Get latest run
    latest_resp = await client.get("/api/v1/evaluation/latest")
    assert latest_resp.status_code == 200
    assert latest_resp.json()["evaluation_run_id"] == eval_run_id

    # 4. Export JSON
    json_export = await client.get(f"/api/v1/evaluation/runs/{eval_run_id}/export?format=json")
    assert json_export.status_code == 200
    assert "application/json" in json_export.headers.get("content-type", "")
    assert "evaluation_run_id" in json_export.text

    # 5. Export CSV
    csv_export = await client.get(f"/api/v1/evaluation/runs/{eval_run_id}/export?format=csv")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers.get("content-type", "")
    assert "Scenario ID,Scenario Name" in csv_export.text
