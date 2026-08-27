import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, VectorType


class Article(Base, TimestampMixin):
    """
    Ingested article or fragment metadata.
    LEGAL REQUIREMENT: Store metadata, extracted claims, and short excerpts with attribution only, NEVER full text.
    """
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", index=True)  # en, hi, ta
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Excerpt only - never full article text
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    attribution_text: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Multilingual embedding vector (384-dimensional by default)
    embedding: Mapped[Optional[list]] = mapped_column(VectorType(384), nullable=True)
    
    # Syndication & originality
    is_original_reporting: Mapped[bool] = mapped_column(Boolean, default=True)
    syndication_origin_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="articles")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="article", cascade="all, delete-orphan")
    stories: Mapped[List["Story"]] = relationship("Story", secondary="story_articles", back_populates="articles")
