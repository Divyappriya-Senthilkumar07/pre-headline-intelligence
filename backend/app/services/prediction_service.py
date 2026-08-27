import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.story import Story
from app.models.article import Article
from app.models.graph import Entity
from app.models.prediction import Prediction
from app.models.contradiction import Contradiction
from app.services.contradiction_service import ContradictionGateResult

logger = logging.getLogger(__name__)


class HistoricalPatternData(BaseModel):
    has_historical_match: bool = False
    sample_size: int = 0
    historical_progression_hours: Optional[float] = None
    support_level: str = "LIMITED_HISTORICAL_DATA"
    historical_note: str = "No historical precursor patterns recorded for this entity domain."


class PredictionResult(BaseModel):
    id: str
    story_id: str
    formation_probability: float = Field(ge=0.0, le=1.0)
    impact_score: float = Field(ge=0.0, le=1.0)
    impact_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    current_stage: str  # EARLY, REGIONAL, NATIONAL, MAINSTREAM
    predicted_next_stage: str  # REGIONAL, NATIONAL, MAINSTREAM, PEAK
    trajectory_confidence: float = Field(ge=0.0, le=1.0)
    trajectory_reasoning: str
    prediction_status: str  # ELIGIBLE, BLOCKED, INSUFFICIENT_DATA
    blocked_reason: Optional[str] = None
    contradiction_id: Optional[str] = None
    historical_pattern: HistoricalPatternData
    explanation: str
    model_version: str = "v1.0-explainable-heuristic"
    created_at: datetime


class PredictionService:
    """
    Agent 7 — Story Trajectory and Impact Prediction Service
    Computes separate Probability, Impact, and Trajectory without black-box opacity.
    Strictly integrates the Hard Contradiction Gate.
    """

    CRITICAL_ENTITY_TYPES = {"REGULATOR", "GOVERNMENT", "MINISTRY", "COURT", "CRITICAL_INFRASTRUCTURE"}
    HIGH_IMPACT_KEYWORDS = {
        "inspection", "probe", "audit", "banned", "shutdown", "closure", "penalty",
        "leak", "contamination", "protest", "strike", "resignation", "charges",
        "ஆய்வு", "தடை", "விசாரணை", "நிறுத்தம்", "जांच", "प्रतिबंध", "छापा"
    }

    @classmethod
    def calculate_probability(
        cls,
        formation_score: float,
        independence_score: float,
        cross_language_score: float,
        evidence_strength_score: float,
    ) -> float:
        """
        Calibrated Probability calculation:
        35% Formation Score + 25% Independence Score + 20% Cross-Language Corroboration + 20% Evidence Strength
        """
        norm_formation = min(1.0, max(0.0, formation_score / 100.0 if formation_score > 1.0 else formation_score))
        norm_cross_lang = min(1.0, max(0.0, cross_language_score / 100.0 if cross_language_score > 1.0 else cross_language_score))
        norm_evidence = min(1.0, max(0.0, evidence_strength_score / 100.0 if evidence_strength_score > 1.0 else evidence_strength_score))
        norm_indep = min(1.0, max(0.0, independence_score))

        prob = (
            0.35 * norm_formation +
            0.25 * norm_indep +
            0.20 * norm_cross_lang +
            0.20 * norm_evidence
        )
        return round(min(1.0, max(0.0, prob)), 3)

    @classmethod
    def calculate_impact(cls, entities: List[Entity], articles: List[Article]) -> tuple[float, str]:
        """
        Calculates impact score (0.0 - 1.0) and categorical level (LOW, MEDIUM, HIGH, CRITICAL).
        """
        impact_points = 0.20  # Base significance

        # Check entity severity
        has_regulator = any(e.entity_type.upper() in cls.CRITICAL_ENTITY_TYPES for e in entities)
        if has_regulator:
            impact_points += 0.35

        # Check high impact keywords in title/excerpts
        text_corpus = " ".join([f"{a.title} {a.excerpt}" for a in articles]).lower()
        keyword_matches = sum(1 for kw in cls.HIGH_IMPACT_KEYWORDS if kw in text_corpus)
        if keyword_matches >= 3:
            impact_points += 0.30
        elif keyword_matches >= 1:
            impact_points += 0.15

        # Cross-regional reach
        distinct_domains = len(set(a.url.split("/")[2] for a in articles if "://" in a.url))
        if distinct_domains >= 3:
            impact_points += 0.15

        impact_score = round(min(1.0, max(0.1, impact_points)), 2)

        if impact_score >= 0.80:
            level = "CRITICAL"
        elif impact_score >= 0.60:
            level = "HIGH"
        elif impact_score >= 0.40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return impact_score, level

    @classmethod
    def determine_trajectory(
        cls,
        articles: List[Article],
        languages: List[str],
        independent_sources_count: int,
    ) -> tuple[str, str, float, str]:
        """
        Estimates trajectory progression:
        EARLY → REGIONAL → NATIONAL → MAINSTREAM
        """
        lang_count = len(set(languages))
        article_count = len(articles)

        if independent_sources_count >= 4 or (lang_count >= 3 and article_count >= 4):
            current = "NATIONAL"
            next_stage = "MAINSTREAM"
            conf = 0.88
            reason = f"Cross-regional coverage established across {lang_count} languages and {independent_sources_count} independent sources; mainstream syndication likely."
        elif independent_sources_count >= 2 or (lang_count >= 2 and article_count >= 2):
            current = "REGIONAL"
            next_stage = "NATIONAL"
            conf = 0.80
            reason = f"Multilingual regional reporting converging across {independent_sources_count} independent outlets. Approaching national wire pickup."
        else:
            current = "EARLY"
            next_stage = "REGIONAL"
            conf = 0.70
            reason = f"Early localized signal detected in {languages[0] if languages else 'local'} media. Monitoring for cross-source corroboration."

        return current, next_stage, conf, reason

    @classmethod
    async def generate_prediction(
        cls,
        db: AsyncSession,
        story: Story,
        articles: List[Article],
        entities: List[Entity],
        contradiction_gate: Optional[ContradictionGateResult] = None,
    ) -> PredictionResult:
        """
        Computes explainable prediction and persists to the database.
        Enforces hard Contradiction Gate immediately.
        """
        now = datetime.now(timezone.utc)
        languages = story.languages or [a.language for a in articles if a.language] or ["en"]

        # 1. Hard Contradiction Gate Check
        is_blocked = (
            story.contradiction_status == "PREDICTION_BLOCKED" or
            story.prediction_eligible is False or
            (contradiction_gate is not None and contradiction_gate.contradiction_status == "PREDICTION_BLOCKED")
        )

        # 2. Compute Probability and Impact
        prob = cls.calculate_probability(
            formation_score=story.formation_score or 0.0,
            independence_score=story.independence_score or 0.0,
            cross_language_score=story.cross_language_score or 0.0,
            evidence_strength_score=story.evidence_strength_score or 0.0,
        )
        impact_score, impact_level = cls.calculate_impact(entities=entities, articles=articles)
        curr_stage, next_stage, traj_conf, traj_reason = cls.determine_trajectory(
            articles=articles,
            languages=languages,
            independent_sources_count=story.independent_sources_count or 1,
        )

        hist_pattern = HistoricalPatternData(
            has_historical_match=False,
            sample_size=0,
            historical_progression_hours=None,
            support_level="LIMITED_HISTORICAL_DATA",
            historical_note="Insufficient verified historical precursor data for this specific entity pair.",
        )

        if is_blocked:
            prediction_status = "BLOCKED"
            blocked_reason = "LOAD_BEARING_CONTRADICTION"
            explanation = (
                "PREDICTION HALTED: Load-bearing factual contradiction detected between primary sources. "
                "Downstream projection is suspended until conflicting claims are resolved."
            )
            # Find contradiction id if available
            res_c = await db.execute(
                select(Contradiction).where(
                    Contradiction.story_id == story.id,
                    Contradiction.is_load_bearing == True,
                    Contradiction.status.in_(["OPEN", "UNRESOLVED"])
                )
            )
            open_contra = res_c.scalars().first()
            contra_id = open_contra.id if open_contra else None
        else:
            prediction_status = "ELIGIBLE"
            blocked_reason = None
            contra_id = None
            explanation = (
                f"Trajectory projected from {curr_stage} to {next_stage} with probability {int(prob * 100)}% "
                f"and {impact_level} impact, supported by {story.independent_sources_count or 1} independent source(s)."
            )

        # 3. Upsert or create Prediction DB record
        res_pred = await db.execute(select(Prediction).where(Prediction.story_id == story.id))
        pred_db = res_pred.scalars().first()

        if not pred_db:
            pred_db = Prediction(
                story_id=story.id,
                formation_probability=prob if not is_blocked else 0.0,
                probability=prob if not is_blocked else 0.0,
                impact_score=impact_score,
                impact=impact_score,
                impact_level=impact_level,
                current_stage=curr_stage,
                predicted_next_stage=next_stage,
                trajectory_stage=curr_stage,
                trajectory_confidence=traj_conf,
                trajectory_reasoning=traj_reason if not is_blocked else "Halted by Contradiction Gate",
                prediction_status=prediction_status,
                blocked_reason=blocked_reason,
                contradiction_id=contra_id,
                is_halted=is_blocked,
                halt_reason=blocked_reason,
                historical_pattern_support=hist_pattern.model_dump(),
                explanation=explanation,
            )
            db.add(pred_db)
        else:
            pred_db.formation_probability = prob if not is_blocked else 0.0
            pred_db.probability = prob if not is_blocked else 0.0
            pred_db.impact_score = impact_score
            pred_db.impact = impact_score
            pred_db.impact_level = impact_level
            pred_db.current_stage = curr_stage
            pred_db.predicted_next_stage = next_stage
            pred_db.trajectory_stage = curr_stage
            pred_db.trajectory_confidence = traj_conf
            pred_db.trajectory_reasoning = traj_reason if not is_blocked else "Halted by Contradiction Gate"
            pred_db.prediction_status = prediction_status
            pred_db.blocked_reason = blocked_reason
            pred_db.contradiction_id = contra_id
            pred_db.is_halted = is_blocked
            pred_db.halt_reason = blocked_reason
            pred_db.historical_pattern_support = hist_pattern.model_dump()
            pred_db.explanation = explanation

        await db.commit()
        await db.refresh(pred_db)

        return PredictionResult(
            id=pred_db.id,
            story_id=pred_db.story_id,
            formation_probability=pred_db.formation_probability,
            impact_score=pred_db.impact_score,
            impact_level=pred_db.impact_level,
            current_stage=pred_db.current_stage,
            predicted_next_stage=pred_db.predicted_next_stage,
            trajectory_confidence=pred_db.trajectory_confidence,
            trajectory_reasoning=pred_db.trajectory_reasoning or "",
            prediction_status=pred_db.prediction_status,
            blocked_reason=pred_db.blocked_reason,
            contradiction_id=pred_db.contradiction_id,
            historical_pattern=hist_pattern,
            explanation=pred_db.explanation or "",
            created_at=pred_db.created_at,
        )
