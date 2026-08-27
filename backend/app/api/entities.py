from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.graph import Entity, GraphEdge

router = APIRouter(prefix="/entities", tags=["Media Event Graph"])


class EntityDetailResponse(BaseModel):
    id: str
    name: str
    canonical_name: str
    entity_type: str
    aliases: List[str] = Field(default_factory=list)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    connected_edges: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("", response_model=List[EntityDetailResponse], summary="List Graph Entities")
async def list_entities(limit: int = 50, db: AsyncSession = Depends(get_db)) -> List[EntityDetailResponse]:
    res = await db.execute(select(Entity).limit(limit))
    entities = res.scalars().all()
    return [
        EntityDetailResponse(
            id=e.id,
            name=e.name,
            canonical_name=e.canonical_name,
            entity_type=e.entity_type,
            aliases=e.aliases,
            metadata_json=e.metadata_json or {},
        )
        for e in entities
    ]


@router.get("/{entity_id}", response_model=EntityDetailResponse, summary="Get Entity Details and Graph Neighbors")
async def get_entity_detail(entity_id: str, db: AsyncSession = Depends(get_db)) -> EntityDetailResponse:
    res = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = res.scalars().first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found.")

    edge_res = await db.execute(
        select(GraphEdge).where(
            (GraphEdge.source_node_id == entity_id) | (GraphEdge.target_node_id == entity_id)
        )
    )
    edges = edge_res.scalars().all()

    return EntityDetailResponse(
        id=entity.id,
        name=entity.name,
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        aliases=entity.aliases,
        metadata_json=entity.metadata_json or {},
        connected_edges=[
            {
                "source": e.source_node_id,
                "target": e.target_node_id,
                "relation": e.edge_type,
                "weight": e.weight,
            }
            for e in edges
        ],
    )
