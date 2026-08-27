import uuid
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.claim import Claim
from app.models.contradiction import Contradiction
from app.services.embedding_service import MultilingualEmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class ContradictionGateResult:
    story_id: str
    contradiction_status: str  # CLEAR, CONFLICT_DETECTED, PREDICTION_BLOCKED, RESOLVED
    prediction_eligible: bool
    is_halted: bool
    active_contradictions_count: int
    load_bearing_conflicts_count: int
    contradictions: List[Contradiction] = field(default_factory=list)
    gate_reason: str = ""


class ContradictionService:
    """
    Agent 5 — Claim Comparison, Contradiction Detection & Hard Contradiction Gate.
    Non-Negotiable Principle: A load-bearing contradiction MUST halt predictions at code level.
    """

    # Antonym / Direct Conflict Polarity Pairs
    POLARITY_CONFLICT_PAIRS = [
        ("approved", "rejected"),
        ("approved", "denied"),
        ("passed", "failed"),
        ("sanctioned", "halted"),
        ("initiated", "terminated"),
        ("guilty", "cleared"),
        ("investigated", "cleared"),
        ("confirmed", "denied"),
        ("agreed", "refused"),
        ("expansion approved", "expansion halted"),
        ("ஆய்வு உறுதி", "ஆய்வு மறுப்பு"),  # Tamil: Inspection confirmed vs denied
        ("அனுமதி வழங்கப்பட்டது", "அனுமதி மறுக்கப்பட்டது"), # Tamil: Approval granted vs rejected
        ("अनुमति दी", "अनुमति रद्द"),  # Hindi: Approval given vs cancelled
        ("निरीक्षण हुआ", "निरीक्षण से इनकार"), # Hindi: Inspection occurred vs denied
    ]

    LOAD_BEARING_KEYWORDS = [
        "approved", "rejected", "investigated", "raid", "closure", "sanction",
        "penalty", "banned", "cleared", "cancelled", "lawsuit", "verdict",
        "அனுமதி", "மறுப்பு", "ஆய்வு", "தடை", "ரத்து",
        "मंजूरी", "रद्द", "निरीक्षण", "प्रतिबंध", "जांच"
    ]

    @classmethod
    def extract_claims_from_article(cls, article: Article) -> List[Claim]:
        """Extracts structured candidate claims and identifies load-bearing statements."""
        claims: List[Claim] = []
        text = f"{article.title}. {article.excerpt}"
        sentences = [s.strip() for s in re.split(r"[.।!?]+", text) if len(s.strip()) > 10]
        
        seen = set()
        unique_sentences = []
        for s in sentences:
            s_clean = s.lower().strip()
            if s_clean not in seen:
                seen.add(s_clean)
                unique_sentences.append(s)

        for s in unique_sentences:
            s_lower = s.lower()
            is_load_bearing = any(k in s_lower for k in cls.LOAD_BEARING_KEYWORDS)
            
            # Determine claim type
            if "official" in s_lower or "spokesperson" in s_lower or "board" in s_lower:
                c_type = "OFFICIAL_STATEMENT"
            elif "confirmed" in s_lower or "ordered" in s_lower or "issued" in s_lower:
                c_type = "RULING"
            elif "alleged" in s_lower or "reported" in s_lower:
                c_type = "ALLEGATION"
            else:
                c_type = "FACT"

            claim = Claim(
                id=str(uuid.uuid4()),
                article_id=article.id,
                statement=s,
                claim_type=c_type,
                is_load_bearing=is_load_bearing,
                confidence=0.88 if is_load_bearing else 0.75,
                language=article.language or "en",
                metadata_json={"source": article.attribution_text},
            )
            claims.append(claim)

        return claims

    @classmethod
    def detect_conflicts_between_claims(
        cls,
        claims: List[Claim],
        story_id: str,
    ) -> List[Contradiction]:
        """
        Compares claims to identify direct load-bearing contradictions.
        Does not flag trivial wording variations.
        """
        contradictions: List[Contradiction] = []
        embedder = MultilingualEmbeddingService()

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1, c2 = claims[i], claims[j]
                if c1.article_id == c2.article_id:
                    continue  # Skip claims from identical article

                s1_lower = c1.statement.lower()
                s2_lower = c2.statement.lower()

                # 1. Check direct polarity conflict
                has_polarity_clash = False
                clash_pair_name = ""
                for pos, neg in cls.POLARITY_CONFLICT_PAIRS:
                    if (pos in s1_lower and neg in s2_lower) or (neg in s1_lower and pos in s2_lower):
                        has_polarity_clash = True
                        clash_pair_name = f"'{pos}' vs '{neg}'"
                        break

                # 2. Check explicit negation ("not", "denied", "false") with high semantic similarity
                is_direct_negation = False
                if not has_polarity_clash:
                    if (" not " in s1_lower and " not " not in s2_lower) or (" not " in s2_lower and " not " not in s1_lower):
                        # Verify they are discussing the same subject/action
                        clean1 = s1_lower.replace(" not ", " ").replace(" no ", " ")
                        clean2 = s2_lower.replace(" not ", " ").replace(" no ", " ")
                        v1 = embedder.embed_text(clean1)
                        v2 = embedder.embed_text(clean2)
                        sim = embedder.cosine_similarity(v1, v2)
                        if sim >= 0.75:
                            is_direct_negation = True
                            clash_pair_name = "Direct factual negation"

                if has_polarity_clash or is_direct_negation:
                    is_load_bearing = c1.is_load_bearing or c2.is_load_bearing
                    severity = "CRITICAL" if is_load_bearing else "MODERATE"
                    
                    contradiction = Contradiction(
                        id=str(uuid.uuid4()),
                        story_id=story_id,
                        claim_a_id=c1.id,
                        claim_b_id=c2.id,
                        is_load_bearing=is_load_bearing,
                        status="OPEN",
                        severity=severity,
                        description=f"Direct load-bearing contradiction ({clash_pair_name}): Source A asserts '{c1.statement}' while Source B asserts conflicting '{c2.statement}'.",
                        halted_prediction=is_load_bearing,
                        conflict_metadata={
                            "clash_type": clash_pair_name,
                            "claim_a_statement": c1.statement,
                            "claim_b_statement": c2.statement,
                            "claim_a_language": c1.language,
                            "claim_b_language": c2.language,
                            "detected_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    contradictions.append(contradiction)

        return contradictions

    @classmethod
    async def evaluate_contradiction_gate(
        cls,
        db: AsyncSession,
        story_id: str,
        articles: List[Article],
    ) -> ContradictionGateResult:
        """
        Executes the Hard Contradiction Gate on a Story.
        If an open load-bearing contradiction exists, prediction_eligible is set to FALSE
        and contradiction_status is set to PREDICTION_BLOCKED.
        """
        # 1. Fetch or extract claims for articles
        article_ids = [a.id for a in articles]
        res_claims = await db.execute(select(Claim).where(Claim.article_id.in_(article_ids)))
        existing_claims = res_claims.scalars().all()

        all_claims = list(existing_claims)
        if not existing_claims:
            for art in articles:
                extracted = cls.extract_claims_from_article(art)
                for c in extracted:
                    db.add(c)
                all_claims.extend(extracted)
            await db.flush()

        # 2. Check existing Contradiction records in DB
        res_contra = await db.execute(select(Contradiction).where(Contradiction.story_id == story_id))
        db_contradictions = res_contra.scalars().all()

        # 3. Detect new conflicts if none persisted yet
        all_contradictions = list(db_contradictions)
        if not db_contradictions:
            new_conflicts = cls.detect_conflicts_between_claims(all_claims, story_id)
            for con in new_conflicts:
                db.add(con)
            all_contradictions.extend(new_conflicts)
            await db.flush()

        # 4. HARD CONTRADICTION GATE CONTROL FLOW
        open_load_bearing = [
            c for c in all_contradictions
            if c.is_load_bearing and c.status in ["OPEN", "UNRESOLVED"]
        ]
        open_non_load_bearing = [
            c for c in all_contradictions
            if not c.is_load_bearing and c.status in ["OPEN", "UNRESOLVED"]
        ]

        if open_load_bearing:
            status = "PREDICTION_BLOCKED"
            prediction_eligible = False
            is_halted = True
            reason = f"Prediction halted — {len(open_load_bearing)} unresolved load-bearing contradiction(s) detected across reporting sources."
        elif open_non_load_bearing:
            status = "CONFLICT_DETECTED"
            prediction_eligible = True
            is_halted = False
            reason = f"Non-load-bearing conflict detected ({len(open_non_load_bearing)} minor items); prediction permitted with caution."
        else:
            status = "CLEAR" if not all_contradictions else "RESOLVED"
            prediction_eligible = True
            is_halted = False
            reason = "No unresolved contradictions detected across supporting sources."

        logger.info(f"[ContradictionGate] Story {story_id} status={status} eligible={prediction_eligible}")

        return ContradictionGateResult(
            story_id=story_id,
            contradiction_status=status,
            prediction_eligible=prediction_eligible,
            is_halted=is_halted,
            active_contradictions_count=len(open_load_bearing) + len(open_non_load_bearing),
            load_bearing_conflicts_count=len(open_load_bearing),
            contradictions=all_contradictions,
            gate_reason=reason,
        )
