import uuid
from typing import List, Optional
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Watchlist(Base, TimestampMixin):
    """Tracked entities and keywords configured by an analyst."""
    __tablename__ = "watchlists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    entities: Mapped[list] = mapped_column(JSON, default=list)  # list of entity names/IDs
    keywords: Mapped[list] = mapped_column(JSON, default=list)  # list of keyword filters
    languages: Mapped[list] = mapped_column(JSON, default=lambda: ["en", "hi", "ta"])  # Tamil, Hindi, English
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlists")
