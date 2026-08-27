from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.article import Article
from app.models.graph import GraphEdge, Entity, Event

router = APIRouter(prefix="/articles", tags=["Articles & Graph"])


class ArticleDetailResponse(BaseModel):
    id: str
    title: str
    url: str
    source_name: str
    language: str
    published_at: datetime
    excerpt: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    mentioned_entities: List[Dict[str, Any]] = Field(default_factory=list)
    described_events: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("", response_model=List[ArticleDetailResponse], summary="List Ingested Articles")
async def list_articles(limit: int = 50, db: AsyncSession = Depends(get_db)) -> List[ArticleDetailResponse]:
    res = await db.execute(select(Article).order_by(Article.published_at.desc()).limit(limit))
    articles = res.scalars().all()
    return [
        ArticleDetailResponse(
            id=a.id,
            title=a.title,
            url=a.url,
            source_name=a.attribution_text,
            language=a.language or "en",
            published_at=a.published_at,
            excerpt=a.excerpt,
            metadata_json=a.metadata_json or {},
        )
        for a in articles
    ]


@router.get("/{article_id}", response_model=ArticleDetailResponse, summary="Get Article Details & Graph Relations")
async def get_article_detail(article_id: str, db: AsyncSession = Depends(get_db)) -> ArticleDetailResponse:
    res = await db.execute(select(Article).where(Article.id == article_id))
    article = res.scalars().first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found.")

    # Fetch mentioned entities
    ent_res = await db.execute(
        select(Entity).join(GraphEdge, GraphEdge.target_node_id == Entity.id).where(
            GraphEdge.source_node_id == article_id,
            GraphEdge.edge_type == "mentions",
        )
    )
    entities = ent_res.scalars().all()

    # Fetch described events
    ev_res = await db.execute(
        select(Event).join(GraphEdge, GraphEdge.target_node_id == Event.id).where(
            GraphEdge.source_node_id == article_id,
            GraphEdge.edge_type == "describes",
        )
    )
    events = ev_res.scalars().all()

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        url=article.url,
        source_name=article.attribution_text,
        language=article.language or "en",
        published_at=article.published_at,
        excerpt=article.excerpt,
        metadata_json=article.metadata_json or {},
        mentioned_entities=[
            {"id": e.id, "name": e.name, "canonical_name": e.canonical_name, "entity_type": e.entity_type}
            for e in entities
        ],
        described_events=[
            {"id": ev.id, "title": ev.title, "event_type": ev.event_type, "location": ev.location}
            for ev in events
        ],
    )
