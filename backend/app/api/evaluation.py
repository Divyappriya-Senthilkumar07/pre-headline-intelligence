from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.replay import EvaluationRun
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarking"])


class EvaluationRunRequest(BaseModel):
    dataset_version: str = Field(default="v1.0.0", description="Evaluation dataset version")
    config_override: Optional[Dict[str, Any]] = None


@router.post("/run", summary="Execute Full Evaluation Run Across Dataset")
async def run_evaluation_benchmark(
    body: EvaluationRunRequest = EvaluationRunRequest(),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes a reproducible evaluation run across all seed scenarios.
    Calculates precision, recall, lead time, calibration bins, and failure root causes.
    """
    res = await EvaluationService.run_full_evaluation(
        db=db,
        dataset_version=body.dataset_version,
        config_override=body.config_override,
    )
    return res


@router.get("/runs", summary="List Past Evaluation Benchmark Runs")
async def list_evaluation_runs(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    res = await db.execute(select(EvaluationRun).order_by(EvaluationRun.started_at.desc()))
    runs = res.scalars().all()
    output = []
    for r in runs:
        output.append({
            "id": r.id,
            "dataset_version": r.dataset_version,
            "code_version": r.code_version,
            "model_version": r.model_version,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "lead_time_avg_hours": r.metrics_summary.get("lead_time", {}).get("average_lead_time_hours"),
            "precision": r.metrics_summary.get("precision_recall", {}).get("precision"),
            "recall": r.metrics_summary.get("precision_recall", {}).get("recall"),
            "scenarios_evaluated": r.metrics_summary.get("scenarios_evaluated", 0),
        })
    return output


@router.get("/latest", summary="Get Most Recent Evaluation Run")
async def get_latest_evaluation_run(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(EvaluationRun).order_by(EvaluationRun.started_at.desc()))
    run = res.scalars().first()
    if not run:
        # Run default evaluation if empty
        return await EvaluationService.run_full_evaluation(db=db)

    return {
        "evaluation_run_id": run.id,
        "dataset_version": run.dataset_version,
        "code_version": run.code_version,
        "model_version": run.model_version,
        "embedding_version": run.embedding_version,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "configuration": run.configuration_snapshot,
        "metrics": run.metrics_summary,
    }


@router.get("/runs/{run_id}", summary="Get Evaluation Run Details")
async def get_evaluation_run_details(run_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(EvaluationRun).where(EvaluationRun.id == run_id))
    run = res.scalars().first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evaluation run '{run_id}' not found.")

    return {
        "evaluation_run_id": run.id,
        "dataset_version": run.dataset_version,
        "code_version": run.code_version,
        "model_version": run.model_version,
        "embedding_version": run.embedding_version,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "configuration": run.configuration_snapshot,
        "metrics": run.metrics_summary,
    }


@router.get("/runs/{run_id}/export", summary="Export Evaluation Run as JSON or CSV")
async def export_evaluation_run_endpoint(
    run_id: str,
    format: str = Query("json", description="Export format: 'json' or 'csv'"),
    db: AsyncSession = Depends(get_db),
):
    try:
        content, media_type, filename = await EvaluationService.export_evaluation_run(
            db=db,
            run_id=run_id,
            export_format=format,
        )
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
