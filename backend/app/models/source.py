import uuid
from typing import List, Optional
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    """News publication, portal, wire service, or official source."""
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="REGIONAL_MEDIA")  # RSS, GDELT, LICENSED_API, GOV_PORTAL, etc.
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    primary_language: Mapped[str] = mapped_column(String(10), default="en")  # en, hi, ta, etc.

    # Relationships
    profile: Mapped[Optional["SourceProfile"]] = relationship("SourceProfile", back_populates="source", uselist=False, cascade="all, delete-orphan")
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="source")


class SourceProfile(Base, TimestampMixin):
    """Independence profile and syndication relationship tracking per source."""
    __tablename__ = "source_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), unique=True, nullable=False)
    independence_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0.0 to 1.0 (1.0 = highly independent original reporting)
    syndication_links: Mapped[list] = mapped_column(JSON, default=list)  # list of source_ids this outlet republishes
    relationship_classification: Mapped[str] = mapped_column(String(50), default="INDEPENDENT")  # ORIGINAL, SYNDICATED, COPIED, INDEPENDENT, UNKNOWN
    corporate_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.7)
    historical_original_rate: Mapped[float] = mapped_column(Float, default=0.5)  # ratio of original vs syndicated

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="profile")
