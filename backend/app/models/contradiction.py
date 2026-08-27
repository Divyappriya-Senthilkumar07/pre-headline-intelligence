import uuid
from typing import Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Contradiction(Base, TimestampMixin):
    """
    Direct conflicts detected between claims across sources.
    If a contradiction is load-bearing, it triggers the Contradiction Gate to halt predictions.
    """
    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id: Mapped[str] = mapped_column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_a_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    claim_b_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    
    # Critical flag: load-bearing conflicts immediately halt prediction in Contradiction Gate
    is_load_bearing: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True)
    # Statuses: OPEN, UNRESOLVED, INVESTIGATING, RESOLVED, DISMISSED
    
    severity: Mapped[str] = mapped_column(String(50), default="CRITICAL")  # CRITICAL, MODERATE, MINOR
    description: Mapped[str] = mapped_column(Text, nullable=False)
    halted_prediction: Mapped[bool] = mapped_column(Boolean, default=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflict_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="contradictions")
    claim_a: Mapped["Claim"] = relationship("Claim", foreign_keys=[claim_a_id])
    claim_b: Mapped["Claim"] = relationship("Claim", foreign_keys=[claim_b_id])
