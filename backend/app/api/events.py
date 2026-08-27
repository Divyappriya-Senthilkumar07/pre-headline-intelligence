from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.graph import Event

router = APIRouter(prefix="/events", tags=["Media Event Graph"])


class EventDetailResponse(BaseModel):
    id: str
    title: str
    event_type: str
    event_timestamp: datetime
    location: Optional[str] = None
    actor: Optional[str] = None
    target: Optional[str] = None
    organizations_involved: List[str] = Field(default_factory=list)
    source_article_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


@router.get("", response_model=List[EventDetailResponse], summary="List Graph Events")
async def list_events(limit: int = 50, db: AsyncSession = Depends(get_db)) -> List[EventDetailResponse]:
    res = await db.execute(select(Event).order_by(Event.event_timestamp.desc()).limit(limit))
    events = res.scalars().all()
    return [
        EventDetailResponse(
            id=ev.id,
            title=ev.title,
            event_type=ev.event_type,
            event_timestamp=ev.event_timestamp,
            location=ev.location,
            actor=ev.actor,
            target=ev.target,
            organizations_involved=ev.organizations_involved,
            source_article_id=ev.source_article_id,
            metadata_json=ev.metadata_json or {},
        )
        for ev in events
    ]


@router.get("/{event_id}", response_model=EventDetailResponse, summary="Get Event Details")
async def get_event_detail(event_id: str, db: AsyncSession = Depends(get_db)) -> EventDetailResponse:
    res = await db.execute(select(Event).where(Event.id == event_id))
    event = res.scalars().first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")

    return EventDetailResponse(
        id=event.id,
        title=event.title,
        event_type=event.event_type,
        event_timestamp=event.event_timestamp,
        location=event.location,
        actor=event.actor,
        target=event.target,
        organizations_involved=event.organizations_involved,
        source_article_id=event.source_article_id,
        metadata_json=event.metadata_json or {},
    )
