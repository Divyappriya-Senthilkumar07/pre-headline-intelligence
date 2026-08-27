import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, VectorType


class Claim(Base, TimestampMixin):
    """
    Extracted granular factual assertions from articles.
    Load-bearing claims are critical to story formation conclusions.
    """
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(50), default="FACT")  # FACT, ALLEGATION, OFFICIAL_STATEMENT, RULING, ANNOUNCEMENT
    
    # Load-bearing claims are critical: if false or contradicted, predictions must halt
    is_load_bearing: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Multilingual embedding for semantic alignment and cross-lingual contradiction detection
    embedding: Mapped[Optional[list]] = mapped_column(VectorType(384), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="claims")
