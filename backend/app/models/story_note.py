import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class StoryNote(Base, TimestampMixin):
    """Analyst note attached to a Story cluster."""
    __tablename__ = "story_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id: Mapped[str] = mapped_column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, default="analyst-default", index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="notes")
    user: Mapped["User"] = relationship("User", back_populates="notes")
