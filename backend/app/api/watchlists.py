import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.watchlist import Watchlist
from app.models.story import Story
from app.models.user import User

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


class WatchlistCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, description="Name of the Watchlist")
    description: Optional[str] = ""
    entities: List[str] = Field(default_factory=list, description="Target entities (e.g., Company X, State Board)")
    keywords: List[str] = Field(default_factory=list, description="Target keywords (e.g., Pollution, Inspection)")
    languages: List[str] = Field(default_factory=lambda: ["ta", "hi", "en"])
    user_id: Optional[str] = "analyst-default"


class WatchlistUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    entities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WatchlistItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    entities: List[str]
    keywords: List[str]
    languages: List[str]
    is_active: bool
    matching_stories_count: int
    created_at: datetime
    updated_at: datetime


async def get_or_create_default_user(db: AsyncSession, user_id: str = "analyst-default") -> User:
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalars().first()
    if not user:
        user = User(
            id=user_id,
            email="analyst@preheadline.intel",
            hashed_password="hashed_placeholder_pwd",
            full_name="Lead Analyst",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def count_matching_stories(db: AsyncSession, entities: List[str], keywords: List[str]) -> int:
    """Calculates how many active stories match this watchlist's entities/keywords."""
    res_stories = await db.execute(select(Story))
    stories = res_stories.scalars().all()
    count = 0
    search_terms = [e.lower() for e in entities] + [k.lower() for k in keywords]
    if not search_terms:
        return len(stories)

    for s in stories:
        text = f"{s.title} {s.why_it_matters or ''} {s.narrative_summary or ''}".lower()
        if any(term in text for term in search_terms):
            count += 1
    return count


@router.get("", response_model=List[WatchlistItemResponse], summary="List All Watchlists")
async def list_watchlists(db: AsyncSession = Depends(get_db)) -> List[WatchlistItemResponse]:
    res = await db.execute(select(Watchlist).order_by(Watchlist.created_at.desc()))
    watchlists = res.scalars().all()

    # If empty, seed default Strategic Corporate & Regulatory Watchlist
    if not watchlists:
        default_user = await get_or_create_default_user(db)
        default_wl = Watchlist(
            id="wl-strategic-01",
            user_id=default_user.id,
            name="Strategic Corporate & Regulatory Watch",
            description="Monitoring industrial compliance, state pollution audits, and regional disclosures.",
            entities=["Company X", "Tamil Nadu Pollution Control Board", "Ministry of Environment"],
            keywords=["compliance", "audit", "inspection", "discharge", "violation"],
            languages=["ta", "hi", "en"],
            is_active=True,
        )
        db.add(default_wl)
        await db.commit()
        await db.refresh(default_wl)
        watchlists = [default_wl]

    output: List[WatchlistItemResponse] = []
    for wl in watchlists:
        match_count = await count_matching_stories(db, wl.entities or [], wl.keywords or [])
        output.append(
            WatchlistItemResponse(
                id=wl.id,
                name=wl.name,
                description=wl.description,
                entities=wl.entities or [],
                keywords=wl.keywords or [],
                languages=wl.languages or ["en"],
                is_active=wl.is_active,
                matching_stories_count=match_count,
                created_at=wl.created_at,
                updated_at=wl.updated_at,
            )
        )
    return output


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED, summary="Create Watchlist")
async def create_watchlist(payload: WatchlistCreateSchema, db: AsyncSession = Depends(get_db)) -> WatchlistItemResponse:
    user = await get_or_create_default_user(db, payload.user_id or "analyst-default")
    
    new_wl = Watchlist(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        entities=payload.entities,
        keywords=payload.keywords,
        languages=payload.languages,
        is_active=True,
    )
    db.add(new_wl)
    await db.commit()
    await db.refresh(new_wl)

    match_count = await count_matching_stories(db, new_wl.entities or [], new_wl.keywords or [])

    return WatchlistItemResponse(
        id=new_wl.id,
        name=new_wl.name,
        description=new_wl.description,
        entities=new_wl.entities or [],
        keywords=new_wl.keywords or [],
        languages=new_wl.languages or ["en"],
        is_active=new_wl.is_active,
        matching_stories_count=match_count,
        created_at=new_wl.created_at,
        updated_at=new_wl.updated_at,
    )


@router.get("/{watchlist_id}", response_model=WatchlistItemResponse, summary="Get Watchlist by ID")
async def get_watchlist(watchlist_id: str, db: AsyncSession = Depends(get_db)) -> WatchlistItemResponse:
    res = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    wl = res.scalars().first()
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Watchlist {watchlist_id} not found.")

    match_count = await count_matching_stories(db, wl.entities or [], wl.keywords or [])

    return WatchlistItemResponse(
        id=wl.id,
        name=wl.name,
        description=wl.description,
        entities=wl.entities or [],
        keywords=wl.keywords or [],
        languages=wl.languages or ["en"],
        is_active=wl.is_active,
        matching_stories_count=match_count,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
    )


@router.put("/{watchlist_id}", response_model=WatchlistItemResponse, summary="Update Watchlist")
async def update_watchlist(
    watchlist_id: str,
    payload: WatchlistUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    res = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    wl = res.scalars().first()
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Watchlist {watchlist_id} not found.")

    if payload.name is not None:
        wl.name = payload.name
    if payload.description is not None:
        wl.description = payload.description
    if payload.entities is not None:
        wl.entities = payload.entities
    if payload.keywords is not None:
        wl.keywords = payload.keywords
    if payload.languages is not None:
        wl.languages = payload.languages
    if payload.is_active is not None:
        wl.is_active = payload.is_active

    await db.commit()
    await db.refresh(wl)

    match_count = await count_matching_stories(db, wl.entities or [], wl.keywords or [])

    return WatchlistItemResponse(
        id=wl.id,
        name=wl.name,
        description=wl.description,
        entities=wl.entities or [],
        keywords=wl.keywords or [],
        languages=wl.languages or ["en"],
        is_active=wl.is_active,
        matching_stories_count=match_count,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
    )


@router.post("/{watchlist_id}/toggle", summary="Toggle Watchlist Active Status")
async def toggle_watchlist_status(watchlist_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    wl = res.scalars().first()
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Watchlist {watchlist_id} not found.")

    wl.is_active = not wl.is_active
    await db.commit()
    return {"watchlist_id": wl.id, "is_active": wl.is_active}


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Watchlist")
async def delete_watchlist(watchlist_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    wl = res.scalars().first()
    if not wl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Watchlist {watchlist_id} not found.")

    await db.delete(wl)
    await db.commit()
    return None
