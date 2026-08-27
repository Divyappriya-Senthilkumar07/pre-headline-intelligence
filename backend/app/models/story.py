import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Table, Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now

# Join table: story_articles
story_articles = Table(
    "story_articles",
    Base.metadata,
    Column("story_id", String(36), ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
    Column("article_id", String(36), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime(timezone=True), default=utc_now),
)

# Join table: story_entities
story_entities = Table(
    "story_entities",
    Base.metadata,
    Column("story_id", String(36), ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", String(36), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Column("relevance_weight", Float, default=1.0),
)


class Story(Base, TimestampMixin):
    """
    Candidate or corroborated story cluster formed from related cross-lingual articles and evidence.
    Includes Phase 3 calibrated Independence, Contradiction Gate, and 6-Dimension Formation Score.
    """
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    why_it_matters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="EMERGING", index=True)
    # Statuses: EMERGING, FORMING, CORROBORATED, MAINSTREAM, HALTED, RESOLVED

    # Phase 3: Overall Intelligence & Formation metrics
    formation_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    formation_status: Mapped[str] = mapped_column(String(50), default="EMERGING", index=True)
    # Formation Statuses: EARLY_SIGNAL, EMERGING, CORROBORATED, BLOCKED_BY_CONTRADICTION

    # Phase 3: Calibrated Source Independence Model
    independence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    source_diversity_score: Mapped[float] = mapped_column(Float, default=0.0)
    temporal_spread_score: Mapped[float] = mapped_column(Float, default=0.0)
    entity_alignment_score: Mapped[float] = mapped_column(Float, default=0.0)
    cross_language_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_strength_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Counts & Languages (Raw article count is strictly separated from independent sources)
    independent_sources_count: Mapped[int] = mapped_column(Integer, default=1)
    total_articles_count: Mapped[int] = mapped_column(Integer, default=1)
    languages: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["ta", "hi", "en"]

    # Phase 3: Hard Contradiction Gate
    contradiction_status: Mapped[str] = mapped_column(String(50), default="CLEAR", index=True)
    # Contradiction Statuses: CLEAR, CONFLICT_DETECTED, PREDICTION_BLOCKED, RESOLVED
    prediction_eligible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Narrative summary grounded in story data
    narrative_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Timeline
    earliest_signal_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    latest_signal_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    estimated_mainstream_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lead_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    articles: Mapped[List["Article"]] = relationship("Article", secondary=story_articles, back_populates="stories")
    entities: Mapped[List["Entity"]] = relationship("Entity", secondary=story_entities, back_populates="stories")
    evidence_chain: Mapped[List["EvidenceChain"]] = relationship("EvidenceChain", back_populates="story", cascade="all, delete-orphan")
    contradictions: Mapped[List["Contradiction"]] = relationship("Contradiction", back_populates="story", cascade="all, delete-orphan")
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="story", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="story", cascade="all, delete-orphan")
    notes: Mapped[List["StoryNote"]] = relationship("StoryNote", back_populates="story", cascade="all, delete-orphan")
