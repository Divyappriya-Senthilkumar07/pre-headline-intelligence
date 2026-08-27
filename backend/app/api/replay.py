from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.replay import ReplayScenario, ReplayEvent, ReplaySnapshot
from app.services.replay_engine import ReplayEngine

router = APIRouter(prefix="/replay", tags=["Historical Replay"])


class ReplayEventItem(BaseModel):
    event_order: int
    original_timestamp: str
    source_name: str
    domain: str
    language: str
    title: str
    excerpt: str
    is_syndicated_copy: bool
    is_load_bearing_contradiction: bool
    expected_relevance: Optional[str] = None


class ReplayScenarioDetail(BaseModel):
    id: str
    name: str
    description: str
    scenario_type: str
    dataset_version: str
    start_time: str
    end_time: str
    expected_outcome: str
    target_milestone: str
    target_milestone_time: Optional[str] = None
    events_count: int
    events: List[ReplayEventItem] = Field(default_factory=list)


class ReplayRunResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: str
    description: str
    expected_outcome: str
    target_milestone: str
    target_milestone_time: Optional[str] = None
    first_valid_alert_time: Optional[str] = None
    first_valid_alert_snapshot: Optional[Dict[str, Any]] = None
    lead_time_hours: Optional[float] = None
    lead_time_minutes: Optional[float] = None
    lead_time_status: str
    total_steps: int
    completed_steps: int
    timeline: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/scenarios", response_model=List[Dict[str, Any]], summary="List All Replay Scenarios")
async def list_replay_scenarios(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    await ReplayEngine.seed_scenarios_if_empty(db)
    res = await db.execute(select(ReplayScenario).order_by(ReplayScenario.id.asc()))
    scenarios = res.scalars().all()

    output = []
    for s in scenarios:
        res_evts = await db.execute(select(ReplayEvent).where(ReplayEvent.scenario_id == s.id))
        evts = res_evts.scalars().all()
        output.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "scenario_type": s.scenario_type,
            "expected_outcome": s.expected_outcome,
            "target_milestone": s.target_milestone,
            "target_milestone_time": s.target_milestone_time.isoformat() if s.target_milestone_time else None,
            "events_count": len(evts),
        })
    return output


@router.get("/scenarios/{scenario_id}", response_model=ReplayScenarioDetail, summary="Get Replay Scenario Details")
async def get_replay_scenario_detail(scenario_id: str, db: AsyncSession = Depends(get_db)) -> ReplayScenarioDetail:
    await ReplayEngine.seed_scenarios_if_empty(db)
    res = await db.execute(select(ReplayScenario).where(ReplayScenario.id == scenario_id))
    s = res.scalars().first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scenario '{scenario_id}' not found.")

    res_evts = await db.execute(
        select(ReplayEvent).where(ReplayEvent.scenario_id == scenario_id).order_by(ReplayEvent.event_order.asc())
    )
    events = res_evts.scalars().all()

    return ReplayScenarioDetail(
        id=s.id,
        name=s.name,
        description=s.description,
        scenario_type=s.scenario_type,
        dataset_version=s.dataset_version,
        start_time=s.start_time.isoformat(),
        end_time=s.end_time.isoformat(),
        expected_outcome=s.expected_outcome,
        target_milestone=s.target_milestone,
        target_milestone_time=s.target_milestone_time.isoformat() if s.target_milestone_time else None,
        events_count=len(events),
        events=[
            ReplayEventItem(
                event_order=e.event_order,
                original_timestamp=e.original_timestamp.isoformat(),
                source_name=e.source_name,
                domain=e.domain,
                language=e.language,
                title=e.title,
                excerpt=e.excerpt,
                is_syndicated_copy=e.is_syndicated_copy,
                is_load_bearing_contradiction=e.is_load_bearing_contradiction,
                expected_relevance=e.expected_relevance,
            )
            for e in events
        ],
    )


@router.post("/scenarios/{scenario_id}/run", response_model=ReplayRunResponse, summary="Execute Chronological Replay")
async def execute_replay(
    scenario_id: str,
    step: Optional[int] = Query(None, description="Replay up to specific chronological step (1-indexed)"),
    db: AsyncSession = Depends(get_db),
) -> ReplayRunResponse:
    """
    Executes historical replay step-by-step with strict look-ahead bias prevention.
    Returns the system belief state at each point and calculates exact lead time against the target milestone.
    """
    try:
        res = await ReplayEngine.run_replay(db=db, scenario_id=scenario_id, up_to_step=step)
        return ReplayRunResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
