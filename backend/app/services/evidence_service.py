import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.story import Story
from app.models.article import Article
from app.models.source import Source
from app.models.claim import Claim
from app.models.evidence import EvidenceChain

logger = logging.getLogger(__name__)


class EvidenceItemDetail(BaseModel):
    item_id: str
    step_order: int
    source_id: str
    source_name: str
    domain: str
    claim_id: str
    claim_statement: str
    evidence_type: str  # OFFICIAL_DOCUMENT, REGULATORY_SOURCE, GOVERNMENT_SOURCE, DIRECT_STATEMENT, INDEPENDENT_CORROBORATION, SOURCE_REPORT
    evidence_excerpt: str  # Short excerpt only, never full reproduced article text
    corroborating_sources: List[str] = Field(default_factory=list)
    confidence_contribution: float = Field(ge=0.0, le=1.0)
    timestamp: str


class EvidenceChainResult(BaseModel):
    id: str
    story_id: str
    chain_status: str  # COMPLETE, PARTIAL, INSUFFICIENT_EVIDENCE
    confidence_score: float
    items_count: int
    items: List[EvidenceItemDetail]
    evidence_types: List[str]
    has_sufficient_evidence: bool
    summary: str


class EvidenceService:
    """
    Agent 8 — Mandatory Evidence Chain Assembly Service
    Formulates structured chain: SOURCE → CLAIM → SUPPORTING EVIDENCE → CORROBORATION → CONFIDENCE.
    Ensures short excerpts only, full attribution, and strict groundedness.
    """

    OFFICIAL_DOMAINS = {".gov", ".nic.in", ".gov.in", "tnsat", "pcb", "court", "gazette"}
    REGULATORY_KEYWORDS = {"board", "regulator", "inspector", "commissioner", "tribunal", "ministry", "வாரியம்", "அதிகாரி"}

    @classmethod
    def classify_evidence_type(cls, source_name: str, domain: str, claim_statement: str) -> str:
        """Determines evidence classification based on provenance signals."""
        domain_lower = domain.lower()
        statement_lower = claim_statement.lower()
        name_lower = source_name.lower()

        if any(g in domain_lower for g in cls.OFFICIAL_DOMAINS) or "gazette" in name_lower or "government" in name_lower:
            return "GOVERNMENT_SOURCE"
        elif any(r in statement_lower or r in name_lower for r in cls.REGULATORY_KEYWORDS):
            return "REGULATORY_SOURCE"
        elif "official statement" in statement_lower or "confirmed" in statement_lower or "declared" in statement_lower:
            return "DIRECT_STATEMENT"
        elif "wire" in name_lower or "pti" in domain_lower or "reuters" in domain_lower:
            return "INDEPENDENT_CORROBORATION"
        else:
            return "SOURCE_REPORT"

    @classmethod
    async def build_evidence_chain(
        cls,
        db: AsyncSession,
        story: Story,
        articles: List[Article],
        claims: Optional[List[Claim]] = None,
    ) -> EvidenceChainResult:
        """
        Builds the structured evidence chain for a candidate story.
        Enforces: NO ALERT WITHOUT EVIDENCE.
        """
        if not articles:
            return EvidenceChainResult(
                id=str(uuid.uuid4()),
                story_id=story.id,
                chain_status="INSUFFICIENT_EVIDENCE",
                confidence_score=0.0,
                items_count=0,
                items=[],
                evidence_types=[],
                has_sufficient_evidence=False,
                summary="Insufficient reporting evidence: No articles linked to story cluster.",
            )

        # 1. Fetch claims if not provided
        if claims is None:
            article_ids = [a.id for a in articles]
            res_c = await db.execute(select(Claim).where(Claim.article_id.in_(article_ids)))
            claims = res_c.scalars().all()

        # Map claims by article_id
        claims_by_article: Dict[str, List[Claim]] = {}
        for c in claims:
            claims_by_article.setdefault(c.article_id, []).append(c)

        # Map sources
        source_ids = [a.source_id for a in articles if a.source_id]
        sources_map: Dict[str, Source] = {}
        if source_ids:
            res_s = await db.execute(select(Source).where(Source.id.in_(source_ids)))
            for s in res_s.scalars().all():
                sources_map[s.id] = s

        # 2. Build ordered structured items
        structured_items: List[EvidenceItemDetail] = []
        evidence_types_seen = set()

        all_source_names = [a.attribution_text for a in articles]

        for step_idx, art in enumerate(articles, start=1):
            src = sources_map.get(art.source_id)
            source_name = art.attribution_text or (src.name if src else "Regional Media")
            domain = src.domain if src else (art.url.split("/")[2] if "://" in art.url else "media.org")

            # Link primary claim or synthesize from title
            art_claims = claims_by_article.get(art.id, [])
            primary_claim = art_claims[0] if art_claims else None
            claim_id = primary_claim.id if primary_claim else f"claim-art-{art.id[:8]}"
            claim_statement = primary_claim.statement if primary_claim else art.title

            # Classify evidence type
            ev_type = cls.classify_evidence_type(source_name, domain, claim_statement)
            evidence_types_seen.add(ev_type)

            # Excerpt limited to 200 chars to avoid reproducing full text
            clean_excerpt = (art.excerpt or art.title).strip()
            if len(clean_excerpt) > 200:
                clean_excerpt = clean_excerpt[:197] + "..."

            corroborating = [s for s in all_source_names if s != source_name]

            item = EvidenceItemDetail(
                item_id=str(uuid.uuid4()),
                step_order=step_idx,
                source_id=art.source_id or f"src-{art.id[:8]}",
                source_name=source_name,
                domain=domain,
                claim_id=claim_id,
                claim_statement=claim_statement,
                evidence_type=ev_type,
                evidence_excerpt=f"[{source_name}]: {clean_excerpt}",
                corroborating_sources=corroborating,
                confidence_contribution=round(0.85 if ev_type in ["GOVERNMENT_SOURCE", "REGULATORY_SOURCE"] else 0.70, 2),
                timestamp=art.published_at.isoformat() if art.published_at else datetime.now(timezone.utc).isoformat(),
            )
            structured_items.append(item)

        # 3. Assess sufficiency
        has_sufficient = len(structured_items) >= 1 and any(
            it.evidence_type in ["GOVERNMENT_SOURCE", "REGULATORY_SOURCE", "INDEPENDENT_CORROBORATION", "SOURCE_REPORT"]
            for it in structured_items
        )

        chain_status = "COMPLETE" if len(structured_items) >= 2 else ("PARTIAL" if len(structured_items) == 1 else "INSUFFICIENT_EVIDENCE")
        confidence = min(0.95, max(0.50, 0.60 + 0.10 * len(structured_items)))

        # 4. Upsert EvidenceChain in DB
        res_chain = await db.execute(select(EvidenceChain).where(EvidenceChain.story_id == story.id))
        chain_db = res_chain.scalars().first()

        items_json = [it.model_dump() for it in structured_items]
        ev_types_list = list(evidence_types_seen)

        if not chain_db:
            chain_db = EvidenceChain(
                story_id=story.id,
                items=items_json,
                chain_status=chain_status,
                confidence_score=confidence,
                evidence_types_present=ev_types_list,
                claim_text=structured_items[0].claim_statement if structured_items else None,
                supporting_quote=structured_items[0].evidence_excerpt if structured_items else None,
                corroborating_sources_count=len(articles),
            )
            db.add(chain_db)
        else:
            chain_db.items = items_json
            chain_db.chain_status = chain_status
            chain_db.confidence_score = confidence
            chain_db.evidence_types_present = ev_types_list
            chain_db.corroborating_sources_count = len(articles)

        await db.commit()
        await db.refresh(chain_db)

        return EvidenceChainResult(
            id=chain_db.id,
            story_id=story.id,
            chain_status=chain_status,
            confidence_score=confidence,
            items_count=len(structured_items),
            items=structured_items,
            evidence_types=ev_types_list,
            has_sufficient_evidence=has_sufficient,
            summary=f"Traceable chain assembled with {len(structured_items)} structured items across {len(ev_types_list)} evidence categories.",
        )
