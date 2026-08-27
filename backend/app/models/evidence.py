import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class EvidenceChain(Base, TimestampMixin):
    """
    Agent 8 — Mandatory Evidence Chain Model (Phase 4 Real Implementation)
    Structured provenance: SOURCE → CLAIM → SUPPORTING EVIDENCE → CORROBORATION → CONFIDENCE.
    """
    __tablename__ = "evidence_chains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id: Mapped[str] = mapped_column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    
    # Structured items list representing the complete chain
    items: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        default=lambda: [],
    )
    
    # Status & Overall Confidence
    chain_status: Mapped[str] = mapped_column(String(50), default="COMPLETE", index=True)  # COMPLETE, PARTIAL, INSUFFICIENT_EVIDENCE
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85)
    evidence_types_present: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Provenance details (excerpts only, no full article texts)
    step_order: Mapped[int] = mapped_column(Integer, default=1)
    evidence_type: Mapped[str] = mapped_column(String(50), default="SOURCE_REPORT")
    claim_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corroborating_sources_count: Mapped[int] = mapped_column(Integer, default=1)
    provenance_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="evidence_chain")
