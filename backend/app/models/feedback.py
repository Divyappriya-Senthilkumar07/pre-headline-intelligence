import uuid
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Feedback(Base, TimestampMixin):
    """
    Analyst feedback on early alerts feeding the continuous re-ranking and relevance model.
    """
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[str] = mapped_column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_positive: Mapped[bool] = mapped_column(Boolean, default=True)
    score: Mapped[int] = mapped_column(Integer, default=1)  # 1 (thumbs up) or -1 (thumbs down)
    feedback_type: Mapped[str] = mapped_column(String(50), default="ACCURATE_FORMATION")
    # Types: ACCURATE_FORMATION, FALSE_POSITIVE, NOISE, MISSED_CONTRADICTION, TIMING_TOO_LATE
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="feedbacks")
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")
