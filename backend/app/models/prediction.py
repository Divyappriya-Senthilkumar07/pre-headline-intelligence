import uuid
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Prediction(Base, TimestampMixin):
    """
    Agent 7 — Prediction Model (Phase 4 Real Implementation)
    Separately represents Probability and Impact, Trajectory progression,
    and enforces the Hard Contradiction Gate.
    """
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id: Mapped[str] = mapped_column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 1. Formation Probability & Impact Score (strictly kept separate)
    formation_score: Mapped[float] = mapped_column(Float, default=0.0)
    formation_probability: Mapped[float] = mapped_column(Float, default=0.5)
    impact_score: Mapped[float] = mapped_column(Float, default=0.5)
    impact_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Compatibility aliases
    probability: Mapped[float] = mapped_column(Float, default=0.5)
    impact: Mapped[float] = mapped_column(Float, default=0.5)

    # 2. Trajectory stages & reasoning
    current_stage: Mapped[str] = mapped_column(String(50), default="EARLY")  # EARLY, REGIONAL, NATIONAL, MAINSTREAM
    predicted_next_stage: Mapped[str] = mapped_column(String(50), default="REGIONAL")  # REGIONAL, NATIONAL, MAINSTREAM, PEAK
    trajectory_stage: Mapped[str] = mapped_column(String(50), default="EARLY")
    trajectory_confidence: Mapped[float] = mapped_column(Float, default=0.75)
    trajectory_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_mainstream_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 3. Contradiction Gate & Prediction Status
    prediction_status: Mapped[str] = mapped_column(String(50), default="ELIGIBLE", index=True)  # ELIGIBLE, BLOCKED, INSUFFICIENT_DATA
    blocked_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # LOAD_BEARING_CONTRADICTION, MISSING_EVIDENCE
    contradiction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_halted: Mapped[bool] = mapped_column(Boolean, default=False)
    halt_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 4. Historical Pattern & Explanations
    historical_pattern_support: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "has_historical_match": False,
            "sample_size": 0,
            "historical_progression_hours": None,
            "support_level": "LIMITED_HISTORICAL_DATA",
        },
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    theoretical_framework: Mapped[str] = mapped_column(String(100), default="Ansoff Weak-Signal & Hiltunen Model")
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0-explainable-heuristic")

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="predictions")
