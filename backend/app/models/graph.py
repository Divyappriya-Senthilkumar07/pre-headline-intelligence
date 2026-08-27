import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Float, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Entity(Base, TimestampMixin):
    """
    Extracted knowledge graph node (Person, Company, Government, Place, Regulation, etc.).
    Extends GDELT entity representation.
    """
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # PERSON, COMPANY, GOVERNMENT, PLACE, REGULATOR, REGULATION
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    gdelt_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    stories: Mapped[List["Story"]] = relationship("Story", secondary="story_entities", back_populates="entities")


class Event(Base, TimestampMixin):
    """
    Extracted event node representing a real-world occurrence (investigation, product launch, dispute, policy change).
    """
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class GraphEdge(Base, TimestampMixin):
    """
    PostgreSQL adjacency-list table representing graph relationships between entities, events, sources, and claims.
    Includes both standard GDELT-style edges (works_for, investigated_by, reported) and
    proprietary intelligence edges (independence, contradiction, claim_evidence).
    """
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_node_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ENTITY, EVENT, SOURCE, CLAIM, ARTICLE
    target_node_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ENTITY, EVENT, SOURCE, CLAIM, ARTICLE
    edge_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Edge types:
    # Standard: works_for, investigated_by, issued, reported, affiliated_with
    # Proprietary: independence, contradiction, claim_evidence, corroborates
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_graph_edge_source_target", "source_node_id", "target_node_id", "edge_type"),
    )
