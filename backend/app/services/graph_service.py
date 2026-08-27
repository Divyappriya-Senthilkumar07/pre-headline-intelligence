import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.graph import Entity, Event, GraphEdge
from app.models.article import Article
from app.models.source import Source
from app.services.context_service import ExtractedEntityData, ExtractedEventData
from app.services.entity_normalizer import EntityNormalizer

logger = logging.getLogger(__name__)


class GraphService:
    """
    Media Event Graph Engine (PostgreSQL Adjacency List).
    Manages deterministic graph node upserts, edge creation, and bounded multi-hop traversal.
    """

    @classmethod
    async def upsert_entity(
        cls,
        db: AsyncSession,
        canonical_name: str,
        entity_type: str,
        raw_mention: Optional[str] = None,
        confidence: float = 0.90,
    ) -> Entity:
        """
        Deterministically finds or creates an Entity node to prevent duplicate entity creation.
        """
        canonical, key = EntityNormalizer.normalize_entity_name(canonical_name, entity_type)

        res = await db.execute(
            select(Entity).where(
                or_(
                    Entity.canonical_name == canonical,
                    Entity.name == canonical,
                )
            )
        )
        entity = res.scalars().first()

        if entity:
            if raw_mention and raw_mention not in entity.aliases:
                entity.aliases = list(set(entity.aliases + [raw_mention]))
                await db.flush()
            return entity

        aliases = [canonical]
        if raw_mention and raw_mention.lower() != canonical.lower():
            aliases.append(raw_mention)

        entity = Entity(
            id=str(uuid.uuid4()),
            name=canonical,
            canonical_name=canonical,
            entity_type=entity_type,
            aliases=aliases,
            metadata_json={"confidence": confidence, "key": key},
        )
        db.add(entity)
        await db.flush()
        logger.debug(f"[GraphService] Created Entity node: {entity.name} ({entity.entity_type})")
        return entity

    @classmethod
    async def upsert_event(
        cls,
        db: AsyncSession,
        event_data: ExtractedEventData,
        source_article_id: Optional[str] = None,
    ) -> Event:
        """
        Creates or retrieves an Event node in the graph.
        """
        res = await db.execute(
            select(Event).where(
                and_(
                    Event.event_type == event_data.event_type,
                    Event.title == event_data.title,
                )
            )
        )
        event = res.scalars().first()
        if event:
            return event

        event = Event(
            id=str(uuid.uuid4()),
            title=event_data.title,
            event_type=event_data.event_type,
            description=f"Event: {event_data.title}",
            location=event_data.location,
            confidence=event_data.confidence,
            metadata_json={
                "actor": event_data.actor,
                "target": event_data.target,
                "organizations_involved": event_data.organizations_involved,
                "source_article_id": source_article_id,
                "event_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(event)
        await db.flush()
        logger.debug(f"[GraphService] Created Event node: {event.title} ({event.event_type})")
        return event

    @classmethod
    async def add_edge(
        cls,
        db: AsyncSession,
        source_id: str,
        target_id: str,
        relation_type: str,
        source_type: str = "ARTICLE",
        target_type: str = "ENTITY",
        weight: float = 1.0,
        edge_metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphEdge:
        """
        Adds a directed edge between two graph nodes if it doesn't already exist.
        """
        res = await db.execute(
            select(GraphEdge).where(
                and_(
                    GraphEdge.source_node_id == source_id,
                    GraphEdge.target_node_id == target_id,
                    GraphEdge.edge_type == relation_type,
                )
            )
        )
        existing = res.scalars().first()
        if existing:
            return existing

        edge = GraphEdge(
            id=str(uuid.uuid4()),
            source_node_id=source_id,
            source_type=source_type,
            target_node_id=target_id,
            target_type=target_type,
            edge_type=relation_type,
            weight=weight,
            properties=edge_metadata or {},
        )
        db.add(edge)
        await db.flush()
        return edge

    @classmethod
    async def build_article_graph_context(
        cls,
        db: AsyncSession,
        article: Article,
        extracted_entities: List[ExtractedEntityData],
        extracted_events: List[ExtractedEventData],
    ) -> Tuple[List[Entity], List[Event], List[GraphEdge]]:
        """
        Integrates an Article into the Media Event Graph:
        - Upserts entities and creates Article -> mentions -> Entity edges
        - Upserts events and creates Article -> describes -> Event edges
        - Creates inter-entity relationships (investigated_by, located_in, etc.)
        """
        created_entities = []
        created_events = []
        created_edges = []

        # 1. Upsert Entities & Connect
        for ent_data in extracted_entities:
            entity = await cls.upsert_entity(
                db=db,
                canonical_name=ent_data.canonical_name,
                entity_type=ent_data.entity_type,
                raw_mention=ent_data.raw_mention,
                confidence=ent_data.confidence,
            )
            created_entities.append(entity)
            edge = await cls.add_edge(
                db=db,
                source_id=article.id,
                target_id=entity.id,
                relation_type="mentions",
                source_type="ARTICLE",
                target_type="ENTITY",
                weight=ent_data.confidence,
            )
            created_edges.append(edge)

        # 2. Upsert Events & Connect
        for ev_data in extracted_events:
            event = await cls.upsert_event(db=db, event_data=ev_data, source_article_id=article.id)
            created_events.append(event)
            edge = await cls.add_edge(
                db=db,
                source_id=article.id,
                target_id=event.id,
                relation_type="describes",
                source_type="ARTICLE",
                target_type="EVENT",
                weight=ev_data.confidence,
            )
            created_edges.append(edge)

        # 3. Connect Inter-Entity Relationships
        regulators = [e for e in created_entities if e.entity_type in ["REGULATOR", "GOVERNMENT"]]
        companies = [e for e in created_entities if e.entity_type == "COMPANY"]
        places = [e for e in created_entities if e.entity_type == "PLACE"]

        for comp in companies:
            for reg in regulators:
                e = await cls.add_edge(
                    db=db,
                    source_id=comp.id,
                    target_id=reg.id,
                    relation_type="investigated_by",
                    source_type="ENTITY",
                    target_type="ENTITY",
                    weight=0.90,
                )
                created_edges.append(e)

            for pl in places:
                e = await cls.add_edge(
                    db=db,
                    source_id=comp.id,
                    target_id=pl.id,
                    relation_type="located_in",
                    source_type="ENTITY",
                    target_type="ENTITY",
                    weight=0.85,
                )
                created_edges.append(e)

        await db.commit()
        return created_entities, created_events, created_edges

    @classmethod
    async def expand_graph(
        cls,
        db: AsyncSession,
        start_node_id: str,
        max_depth: int = 2,
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """
        Agent 3 — Bounded Graph Expansion:
        Walks outward from start_node_id (Article, Entity, or Event) up to max_depth
        and discovers connected articles, entities, events, and multilingual coverage.
        """
        visited_nodes: Set[str] = {start_node_id}
        frontier: Set[str] = {start_node_id}
        discovered_edges: List[GraphEdge] = []

        for depth in range(max_depth):
            if not frontier:
                break

            res = await db.execute(
                select(GraphEdge).where(
                    or_(
                        GraphEdge.source_node_id.in_(frontier),
                        GraphEdge.target_node_id.in_(frontier),
                    )
                )
            )
            edges = res.scalars().all()
            new_frontier: Set[str] = set()

            for edge in edges:
                discovered_edges.append(edge)
                for nid in [edge.source_node_id, edge.target_node_id]:
                    if nid not in visited_nodes:
                        visited_nodes.add(nid)
                        new_frontier.add(nid)

            frontier = new_frontier
            if len(visited_nodes) >= max_results:
                break

        node_ids = list(visited_nodes)
        
        art_res = await db.execute(select(Article).where(Article.id.in_(node_ids)))
        articles = art_res.scalars().all()

        ent_res = await db.execute(select(Entity).where(Entity.id.in_(node_ids)))
        entities = ent_res.scalars().all()

        ev_res = await db.execute(select(Event).where(Event.id.in_(node_ids)))
        events = ev_res.scalars().all()

        languages = list(set(a.language for a in articles if a.language))

        return {
            "start_node_id": start_node_id,
            "depth_reached": max_depth,
            "total_nodes": len(visited_nodes),
            "articles": articles,
            "entities": entities,
            "events": events,
            "edges": discovered_edges,
            "languages_represented": languages,
        }
