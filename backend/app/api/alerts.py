from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.models.contradiction import Contradiction
from app.services.alert_service import AlertOrchestratorService, AlertItemDetail

router = APIRouter(prefix="/alerts", tags=["Early Intelligence Alerts"])


class AlertFeedbackRequest(BaseModel):
    rating: str = Field(..., description="THUMBS_UP or THUMBS_DOWN")
    notes: Optional[str] = Field(default=None, description="Optional analyst feedback rationale")
    analyst_id: Optional[str] = Field(default="analyst-default")


class AlertFeedbackResponse(BaseModel):
    id: str
    alert_id: str
    rating: str
    is_positive: bool
    notes: Optional[str]
    created_at: datetime


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="ACTIVE | INVESTIGATING | ACKNOWLEDGED | DISMISSED | RESOLVED")
    notes: Optional[str] = None


@router.get("", response_model=List[AlertItemDetail], summary="List Ranked Alerts with Status Filters")
async def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: ACTIVE, INVESTIGATING, ACKNOWLEDGED, DISMISSED, BLOCKED, RESOLVED"),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> List[AlertItemDetail]:
    query = select(Alert).order_by(Alert.ranking_score.desc(), Alert.created_at.desc())
    if status_filter:
        statuses = [s.strip().upper() for s in status_filter.split(",")]
        query = query.where(Alert.status.in_(statuses))
    query = query.limit(limit)

    res = await db.execute(query)
    alerts = res.scalars().all()

    output: List[AlertItemDetail] = []
    for a in alerts:
        output.append(
            AlertItemDetail(
                id=a.id,
                story_id=a.story_id,
                alert_type=a.alert_type,
                headline_in_progress=a.headline_in_progress or a.title,
                why_it_matters=a.why_it_matters,
                urgency=a.urgency,
                probability=a.probability,
                impact=a.impact,
                impact_level=a.impact_level or "MEDIUM",
                ranking_score=a.ranking_score or 0.0,
                ranking_explanation=a.ranking_explanation or "",
                formation_score=a.formation_score,
                independent_source_count=a.independent_source_count,
                language_count=a.language_count,
                languages=a.languages or ["en"],
                evidence_available=a.evidence_available,
                contradiction_status=a.contradiction_status,
                prediction_status=a.prediction_status,
                status=a.status,
                created_at=a.created_at,
            )
        )
    return output


@router.get("/{alert_id}", response_model=AlertItemDetail, summary="Get Alert Detail")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)) -> AlertItemDetail:
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    a = res.scalars().first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found.")

    return AlertItemDetail(
        id=a.id,
        story_id=a.story_id,
        alert_type=a.alert_type,
        headline_in_progress=a.headline_in_progress or a.title,
        why_it_matters=a.why_it_matters,
        urgency=a.urgency,
        probability=a.probability,
        impact=a.impact,
        impact_level=a.impact_level or "MEDIUM",
        ranking_score=a.ranking_score or 0.0,
        ranking_explanation=a.ranking_explanation or "",
        formation_score=a.formation_score,
        independent_source_count=a.independent_source_count,
        language_count=a.language_count,
        languages=a.languages or ["en"],
        evidence_available=a.evidence_available,
        contradiction_status=a.contradiction_status,
        prediction_status=a.prediction_status,
        status=a.status,
        created_at=a.created_at,
    )


@router.post("/{alert_id}/status", response_model=AlertItemDetail, summary="Update Alert Status")
async def update_alert_status(
    alert_id: str,
    body: AlertStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AlertItemDetail:
    res = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found.")

    target_status = body.status.upper()
    valid_statuses = ["ACTIVE", "INVESTIGATING", "ACKNOWLEDGED", "DISMISSED", "BLOCKED", "RESOLVED"]
    if target_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {body.status}")

    # Contradiction Gate Transition Guard:
    # Cannot mark a contradiction-blocked alert as ACTIVE or RESOLVED without resolving the underlying contradiction first.
    if alert.contradiction_status == "PREDICTION_BLOCKED" and target_status in ["ACTIVE", "RESOLVED"]:
        res_contra = await db.execute(
            select(Contradiction).where(
                Contradiction.story_id == alert.story_id,
                Contradiction.is_load_bearing == True,
                Contradiction.status.in_(["OPEN", "UNRESOLVED"])
            )
        )
        unresolved = res_contra.scalars().all()
        if unresolved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot activate or resolve alert while an open load-bearing contradiction exists. Resolve the contradiction first.",
            )

    alert.status = target_status
    await db.commit()
    await db.refresh(alert)

    return AlertItemDetail(
        id=alert.id,
        story_id=alert.story_id,
        alert_type=alert.alert_type,
        headline_in_progress=alert.headline_in_progress or alert.title,
        why_it_matters=alert.why_it_matters,
        urgency=alert.urgency,
        probability=alert.probability,
        impact=alert.impact,
        impact_level=alert.impact_level or "MEDIUM",
        ranking_score=alert.ranking_score or 0.0,
        ranking_explanation=alert.ranking_explanation or "",
        formation_score=alert.formation_score,
        independent_source_count=alert.independent_source_count,
        language_count=alert.language_count,
        languages=alert.languages or ["en"],
        evidence_available=alert.evidence_available,
        contradiction_status=alert.contradiction_status,
        prediction_status=alert.prediction_status,
        status=alert.status,
        created_at=alert.created_at,
    )


@router.post("/{alert_id}/feedback", response_model=AlertFeedbackResponse, summary="Submit Analyst Alert Feedback")
async def submit_alert_feedback(
    alert_id: str,
    body: AlertFeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> AlertFeedbackResponse:
    res_a = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = res_a.scalars().first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found.")

    feedback = await AlertOrchestratorService.record_feedback(
        db=db,
        alert_id=alert_id,
        rating=body.rating,
        notes=body.notes,
        analyst_id=body.analyst_id,
    )

    return AlertFeedbackResponse(
        id=feedback.id,
        alert_id=feedback.alert_id,
        rating="THUMBS_UP" if feedback.is_positive else "THUMBS_DOWN",
        is_positive=feedback.is_positive,
        notes=feedback.notes,
        created_at=feedback.created_at,
    )
