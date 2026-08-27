import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, utc_now


class ReplayScenario(Base, TimestampMixin):
    """
    Historical Scenario definition for evaluation and replay benchmarking.
    Ground-truth outcomes are separated from replay inputs.
    """
    __tablename__ = "replay_scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(64), default="EARLY_DETECTION")
    # EARLY_DETECTION, SYNDICATION_TRAP, MULTILINGUAL_CONVERGENCE, CONTRADICTION, FALSE_SIGNAL, MISSED_STORY
    dataset_version: Mapped[str] = mapped_column(String(64), default="v1.0.0")

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    target_story_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Post-hoc ground truth outcome
    expected_outcome: Mapped[str] = mapped_column(String(64), default="MAINSTREAM_HEADLINE")
    # MAINSTREAM_HEADLINE, NATIONAL_PICKUP, REGIONAL_ONLY, DISAPPEARED, FALSE_SIGNAL, CONFLICT_HALTED
    target_milestone: Mapped[str] = mapped_column(String(64), default="MAINSTREAM")
    target_milestone_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    events: Mapped[List["ReplayEvent"]] = relationship("ReplayEvent", back_populates="scenario", cascade="all, delete-orphan", order_by="ReplayEvent.event_order")
    snapshots: Mapped[List["ReplaySnapshot"]] = relationship("ReplaySnapshot", back_populates="scenario", cascade="all, delete-orphan")


class ReplayEvent(Base, TimestampMixin):
    """Single chronological event in a replay scenario."""
    __tablename__ = "replay_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id: Mapped[str] = mapped_column(String(64), ForeignKey("replay_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    original_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="source.org")
    language: Mapped[str] = mapped_column(String(10), default="en")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata for scenario mechanics
    is_syndicated_copy: Mapped[bool] = mapped_column(Boolean, default=False)
    syndication_origin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_load_bearing_contradiction: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_relevance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    scenario: Mapped["ReplayScenario"] = relationship("ReplayScenario", back_populates="events")


class ReplaySnapshot(Base, TimestampMixin):
    """System state snapshot at a specific point in the replay clock."""
    __tablename__ = "replay_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id: Mapped[str] = mapped_column(String(64), ForeignKey("replay_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    replay_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    story_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    story_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    story_state: Mapped[str] = mapped_column(String(64), default="FRAGMENT")

    # Belief State metrics
    formation_score: Mapped[float] = mapped_column(Float, default=0.0)
    independent_sources_count: Mapped[int] = mapped_column(Integer, default=0)
    total_articles_count: Mapped[int] = mapped_column(Integer, default=0)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    contradiction_status: Mapped[str] = mapped_column(String(50), default="CLEAR")
    is_prediction_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    probability: Mapped[float] = mapped_column(Float, default=0.0)
    impact: Mapped[float] = mapped_column(Float, default=0.0)
    urgency: Mapped[float] = mapped_column(Float, default=0.0)
    trajectory_stage: Mapped[str] = mapped_column(String(50), default="EARLY")

    alert_fired: Mapped[bool] = mapped_column(Boolean, default=False)
    is_valid_early_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_available: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_score: Mapped[float] = mapped_column(Float, default=0.0)

    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    scenario: Mapped["ReplayScenario"] = relationship("ReplayScenario", back_populates="snapshots")


class EvaluationRun(Base, TimestampMixin):
    """Versioned and reproducible evaluation benchmark run."""
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"eval-run-{uuid.uuid4().hex[:12]}")
    dataset_version: Mapped[str] = mapped_column(String(64), default="v1.0.0")
    code_version: Mapped[str] = mapped_column(String(64), default="phase6-release")
    model_version: Mapped[str] = mapped_column(String(64), default="gemini-flash-1.5")
    embedding_version: Mapped[str] = mapped_column(String(64), default="all-MiniLM-L6-v2-384d")

    status: Mapped[str] = mapped_column(String(50), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    configuration_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_summary: Mapped[dict] = mapped_column(JSON, default=dict)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
