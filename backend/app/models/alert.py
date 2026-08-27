import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    """
    Agent 9 — Ranked Early Intelligence Alert Model (Phase 4 Real Implementation).
    Emitted only when verified through the mandatory evidence chain and Contradiction Gate.
    """
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id: Mapped[str] = mapped_column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    alert_type: Mapped[str] = mapped_column(String(50), default="EMERGING_STORY")  # EMERGING_STORY, FORMATION_ACCELERATION, REGULATORY_PROBE
    headline_in_progress: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Priority & ranking (Urgency × Probability × Impact)
    urgency: Mapped[float] = mapped_column(Float, default=0.5)
    probability: Mapped[float] = mapped_column(Float, default=0.5)
    impact: Mapped[float] = mapped_column(Float, default=0.5)
    impact_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    ranking_score: Mapped[float] = mapped_column(Float, default=0.125, index=True)  # urgency * probability * impact
    rank_score: Mapped[float] = mapped_column(Float, default=0.125)
    ranking_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Signals & Intelligence Indicators
    formation_score: Mapped[float] = mapped_column(Float, default=0.0)
    formation_confidence: Mapped[str] = mapped_column(String(50), default="MEDIUM")    # Multilingual & Source counts
    independent_source_count: Mapped[int] = mapped_column(Integer, default=1)
    independent_sources_count: Mapped[int] = mapped_column(Integer, default=1)
    language_count: Mapped[int] = mapped_column(Integer, default=1)
    languages: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Gate & Evidence Verification Links
    evidence_chain_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    evidence_available: Mapped[bool] = mapped_column(default=True)
    contradiction_status: Mapped[str] = mapped_column(String(50), default="CLEAR")  # CLEAR, PREDICTION_BLOCKED, RESOLVED
    prediction_status: Mapped[str] = mapped_column(String(50), default="ELIGIBLE")  # ELIGIBLE, BLOCKED
    has_unresolved_contradictions: Mapped[bool] = mapped_column(default=False)
    estimated_lead_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Lifecycle Status
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", index=True)  # ACTIVE, INVESTIGATING, ACKNOWLEDGED, DISMISSED, BLOCKED, RESOLVED
    alert_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="alerts")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="alert", cascade="all, delete-orphan")
