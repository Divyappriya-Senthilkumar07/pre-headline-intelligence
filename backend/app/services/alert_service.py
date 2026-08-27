import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.story import Story
from app.models.article import Article
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert
from app.models.contradiction import Contradiction
from app.models.feedback import Feedback
from app.services.contradiction_service import ContradictionGateResult

logger = logging.getLogger(__name__)


class AlertItemDetail(BaseModel):
    id: str
    story_id: str
    alert_type: str
    headline_in_progress: str
    why_it_matters: str
    urgency: float
    probability: float
    impact: float
    impact_level: str
    ranking_score: float
    ranking_explanation: str
    formation_score: float
    independent_source_count: int
    language_count: int
    languages: List[str]
    evidence_available: bool
    contradiction_status: str
    prediction_status: str
    status: str
    created_at: datetime


class AlertOrchestratorService:
    """
    Agent 9 — Alert Orchestration Service
    Evaluates defense-in-depth eligibility, enforces the server-side Contradiction Gate,
    and computes Urgency × Probability × Impact ranking.
    """

    @classmethod
    def calculate_urgency(
        cls,
        independent_sources: int,
        language_count: int,
        impact_score: float,
        formation_score: float,
    ) -> float:
        """
        Urgency calculation:
        40% Velocity/Sources + 30% Multilingual Spread + 30% Impact
        """
        norm_sources = min(1.0, max(0.2, independent_sources / 4.0))
        norm_lang = min(1.0, max(0.2, language_count / 3.0))
        norm_impact = min(1.0, max(0.1, impact_score))

        urgency = 0.40 * norm_sources + 0.30 * norm_lang + 0.30 * norm_impact
        return round(min(1.0, max(0.1, urgency)), 3)

    @classmethod
    async def evaluate_and_create_alert(
        cls,
        db: AsyncSession,
        story: Story,
        prediction: Optional[Prediction],
        evidence_chain: Optional[EvidenceChain],
        articles: List[Article],
    ) -> Optional[Alert]:
        """
        Defense-in-depth pre-alert validation and creation.
        Guards against missing evidence, blocked predictions, and load-bearing contradictions.
        """
        # 1. Final Server-Side Contradiction Gate Check
        res_contra = await db.execute(
            select(Contradiction).where(
                Contradiction.story_id == story.id,
                Contradiction.is_load_bearing == True,
                Contradiction.status.in_(["OPEN", "UNRESOLVED"])
            )
        )
        open_load_bearing = res_contra.scalars().all()

        is_contradiction_blocked = (
            story.contradiction_status == "PREDICTION_BLOCKED" or
            story.prediction_eligible is False or
            len(open_load_bearing) > 0 or
            (prediction is not None and prediction.prediction_status == "BLOCKED")
        )

        # 2. Check Evidence Chain Sufficiency (NO ALERT WITHOUT EVIDENCE)
        has_insufficient_evidence = (
            evidence_chain is None or
            evidence_chain.chain_status == "INSUFFICIENT_EVIDENCE" or
            not articles
        )

        languages = story.languages or [a.language for a in articles if a.language] or ["en"]
        independent_sources = story.independent_sources_count or 1
        formation_score = story.formation_score or 0.0

        prob = prediction.formation_probability if (prediction and not is_contradiction_blocked) else 0.0
        impact_val = prediction.impact_score if prediction else 0.5
        impact_lvl = prediction.impact_level if prediction else "MEDIUM"

        urgency_val = cls.calculate_urgency(
            independent_sources=independent_sources,
            language_count=len(languages),
            impact_score=impact_val,
            formation_score=formation_score,
        )

        # Ranking score: Urgency × Probability × Impact
        rank_score = round(urgency_val * prob * impact_val, 4)

        headline = f"Emerging: {story.title}"
        why_matters = story.why_it_matters or story.narrative_summary or "Converging multi-source reporting."

        # Determine Alert Lifecycle Status
        if is_contradiction_blocked:
            alert_status = "BLOCKED"
            ranking_expl = "ALERT BLOCKED: Load-bearing contradiction detected. Investigation required."
        elif has_insufficient_evidence:
            alert_status = "BLOCKED"
            ranking_expl = "ALERT BLOCKED: Insufficient structured evidence in provenance chain."
        elif formation_score < 25.0:
            alert_status = "DISMISSED"
            ranking_expl = "Story formation score below actionable intelligence threshold."
        else:
            alert_status = "ACTIVE"
            ranking_expl = f"Ranked #{rank_score} (Urgency: {int(urgency_val*100)}%, Prob: {int(prob*100)}%, Impact: {int(impact_val*100)}%)."

        # 3. Upsert Alert DB Record
        res_alert = await db.execute(select(Alert).where(Alert.story_id == story.id))
        alert_db = res_alert.scalars().first()

        if not alert_db:
            alert_db = Alert(
                story_id=story.id,
                alert_type="EMERGING_STORY",
                headline_in_progress=headline,
                title=headline,
                why_it_matters=why_matters,
                urgency=urgency_val,
                probability=prob,
                impact=impact_val,
                impact_level=impact_lvl,
                ranking_score=rank_score,
                rank_score=rank_score,
                ranking_explanation=ranking_expl,
                formation_score=formation_score,
                formation_confidence="HIGH" if formation_score >= 75 else ("MEDIUM" if formation_score >= 50 else "LOW"),
                independent_source_count=independent_sources,
                language_count=len(languages),
                languages=languages,
                evidence_chain_id=evidence_chain.id if evidence_chain else None,
                evidence_available=not has_insufficient_evidence,
                contradiction_status="PREDICTION_BLOCKED" if is_contradiction_blocked else "CLEAR",
                prediction_status="BLOCKED" if is_contradiction_blocked else "ELIGIBLE",
                has_unresolved_contradictions=is_contradiction_blocked,
                status=alert_status,
            )
            db.add(alert_db)
        else:
            alert_db.headline_in_progress = headline
            alert_db.title = headline
            alert_db.why_it_matters = why_matters
            alert_db.urgency = urgency_val
            alert_db.probability = prob
            alert_db.impact = impact_val
            alert_db.impact_level = impact_lvl
            alert_db.ranking_score = rank_score
            alert_db.rank_score = rank_score
            alert_db.ranking_explanation = ranking_expl
            alert_db.formation_score = formation_score
            alert_db.independent_source_count = independent_sources
            alert_db.language_count = len(languages)
            alert_db.languages = languages
            alert_db.evidence_chain_id = evidence_chain.id if evidence_chain else None
            alert_db.evidence_available = not has_insufficient_evidence
            alert_db.contradiction_status = "PREDICTION_BLOCKED" if is_contradiction_blocked else "CLEAR"
            alert_db.prediction_status = "BLOCKED" if is_contradiction_blocked else "ELIGIBLE"
            alert_db.has_unresolved_contradictions = is_contradiction_blocked
            alert_db.status = alert_status

        await db.commit()
        await db.refresh(alert_db)
        return alert_db

    @classmethod
    async def get_ranked_emerging_stories(cls, db: AsyncSession, limit: int = 50) -> List[AlertItemDetail]:
        """
        Fetches ranked active intelligence feed items sorted by ranking score.
        """
        res = await db.execute(
            select(Alert).order_by(Alert.ranking_score.desc(), Alert.created_at.desc()).limit(limit)
        )
        alerts = res.scalars().all()

        output: List[AlertItemDetail] = []
        for a in alerts:
            output.append(
                AlertItemDetail(
                    id=a.id,
                    story_id=a.story_id,
                    alert_type=a.alert_type,
                    headline_in_progress=a.headline_in_progress or a.title,
                    why_it_matters=a.why_it_matters,
                    urgency=a.urgency,
                    probability=a.probability,
                    impact=a.impact,
                    impact_level=a.impact_level or "MEDIUM",
                    ranking_score=a.ranking_score or 0.0,
                    ranking_explanation=a.ranking_explanation or "",
                    formation_score=a.formation_score,
                    independent_source_count=a.independent_source_count,
                    language_count=a.language_count,
                    languages=a.languages or ["en"],
                    evidence_available=a.evidence_available,
                    contradiction_status=a.contradiction_status,
                    prediction_status=a.prediction_status,
                    status=a.status,
                    created_at=a.created_at,
                )
            )
        return output

    @classmethod
    async def record_feedback(
        cls,
        db: AsyncSession,
        alert_id: str,
        rating: str,
        notes: Optional[str] = None,
        analyst_id: Optional[str] = None,
    ) -> Feedback:
        """Records analyst feedback for an alert."""
        is_pos = (rating.upper() in ["THUMBS_UP", "UP", "POSITIVE", "TRUE"])
        feedback = Feedback(
            alert_id=alert_id,
            user_id=analyst_id or "analyst-seed-01",
            is_positive=is_pos,
            score=1 if is_pos else -1,
            feedback_type="ACCURATE_FORMATION" if is_pos else "FALSE_POSITIVE",
            notes=notes,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback
