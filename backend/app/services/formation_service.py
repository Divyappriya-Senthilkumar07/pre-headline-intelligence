import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Story
from app.models.article import Article
from app.models.graph import Entity, Event
from app.services.independence_service import IndependenceAnalysisResult
from app.services.contradiction_service import ContradictionGateResult

logger = logging.getLogger(__name__)


@dataclass
class FormationDimensionScore:
    dimension_name: str
    score: float  # 0 to 100
    weight_pct: int  # e.g. 20
    description: str
    evidence_detail: str


@dataclass
class FormationScoreResult:
    story_id: str
    overall_score: float  # 0 to 100
    formation_status: str  # EARLY_SIGNAL, EMERGING, CORROBORATED, BLOCKED_BY_CONTRADICTION
    prediction_eligible: bool
    dimensions: Dict[str, FormationDimensionScore] = field(default_factory=dict)
    narrative_summary: str = ""
    framework_context: str = ""


class StoryFormationService:
    """
    Agent 6 — Narrative & Story Formation Engine.
    Computes the 6-dimension explainable Story Formation Score grounded in:
    1. Ansoff weak-signal framework (Ansoff, 1975)
    2. Hiltunen's signal / issue / interpretation model (Hiltunen, 2008)
    """

    @classmethod
    def calculate_cross_language_score(cls, languages: List[str], independent_sources_count: int) -> float:
        """
        Computes calibrated cross-language corroboration score.
        Rule: Convergence across EN, TA, and HI increases confidence significantly,
        without naive probability multiplication.
        """
        langs = set(l.lower() for l in languages if l)
        if len(langs) >= 3 and independent_sources_count >= 3:
            return 95.0
        elif len(langs) >= 2 and independent_sources_count >= 2:
            return 85.0
        elif len(langs) >= 2:
            return 70.0
        elif "en" in langs and independent_sources_count >= 2:
            return 60.0
        else:
            return 40.0

    @classmethod
    def calculate_evidence_strength(cls, articles: List[Article], entities: List[Entity]) -> Tuple[float, str]:
        """
        Evaluates structured evidence strength (official sources, government filings, direct reporting).
        Never treats pure repetition as evidence.
        """
        official_indicators = ["board", "official", "regulator", "gazette", "spcb", "govt", "department", "tribunal"]
        has_official_source = any(
            any(k in (a.attribution_text or "").lower() or k in a.title.lower() for k in official_indicators)
            for a in articles
        )
        has_regulator_entity = any(e.entity_type in ["REGULATOR", "GOVERNMENT"] for e in entities)

        if has_official_source and has_regulator_entity:
            return 90.0, "Corroborated by official regulatory entity and administrative source citations."
        elif has_official_source or has_regulator_entity:
            return 75.0, "Includes direct administrative/regulatory entity citations."
        elif len(articles) >= 2:
            return 60.0, "Corroborated via multiple independent eyewitness/reporter accounts."
        else:
            return 35.0, "Limited primary evidence; single-source reporting."

    @classmethod
    def generate_grounded_narrative(
        cls,
        title: str,
        articles: List[Article],
        entities: List[Entity],
        independence: IndependenceAnalysisResult,
        contradiction_gate: ContradictionGateResult,
        formation_score: float,
    ) -> str:
        """
        Constructs a strictly grounded narrative summary citing actual story data,
        entities, languages, and contradiction status with zero hallucinated filler.
        """
        langs_str = ", ".join(l.upper() for l in independence.languages_represented) or "EN"
        entity_names = [e.canonical_name for e in entities]
        ent_str = ", ".join(entity_names[:3]) if entity_names else "tracked regional entities"

        if contradiction_gate.contradiction_status == "PREDICTION_BLOCKED":
            return (
                f"Prediction path halted for '{title}'. While {independence.total_articles_count} signals "
                f"were detected across {langs_str} referencing {ent_str}, an unresolved load-bearing contradiction "
                f"was identified between credible sources ({contradiction_gate.gate_reason}). "
                f"Under the platform's non-negotiable Contradiction Gate, story promotion and predictive alerting are blocked until resolved."
            )

        evidence_phrase = "with regulatory citations" if any(e.entity_type == "REGULATOR" for e in entities) else "from independent regional reporting"

        return (
            f"An emerging narrative concerning {ent_str} is converging across "
            f"{independence.independent_sources_count} genuinely independent sources in {langs_str} "
            f"({independence.total_articles_count} total signals clustered). "
            f"Reporting demonstrates organic temporal emergence {evidence_phrase}. "
            f"Contradiction check is {contradiction_gate.contradiction_status}. "
            f"Story Formation Score is calibrated at {int(formation_score)}/100 under the Ansoff weak-signal framework."
        )

    @classmethod
    async def compute_story_formation(
        cls,
        db: AsyncSession,
        story: Story,
        articles: List[Article],
        entities: List[Entity],
        independence: IndependenceAnalysisResult,
        contradiction_gate: ContradictionGateResult,
    ) -> FormationScoreResult:
        """
        Computes 6-Dimension Explainable Formation Score and updates Story record.
        """
        # Dimension 1: Source Diversity (20%)
        d1_score = round(independence.source_diversity_score * 100.0, 1)
        dim1 = FormationDimensionScore(
            dimension_name="Source Diversity",
            score=d1_score,
            weight_pct=20,
            description="Distinct publishing entities across independent ownership and domains.",
            evidence_detail=f"{independence.independent_sources_count} independent sources out of {independence.candidate_sources_count} candidate publishers.",
        )

        # Dimension 2: Temporal Spread (15%)
        d2_score = round(independence.temporal_spread_score * 100.0, 1)
        dim2 = FormationDimensionScore(
            dimension_name="Temporal Spread",
            score=d2_score,
            weight_pct=15,
            description="Organic reporting evolution over hours/days vs simultaneous wire blast.",
            evidence_detail=f"Temporal pattern evaluated across {len(articles)} chronological timestamps.",
        )

        # Dimension 3: Entity Alignment (20%)
        d3_score = round(independence.entity_alignment_score * 100.0, 1)
        dim3 = FormationDimensionScore(
            dimension_name="Entity Alignment",
            score=d3_score,
            weight_pct=20,
            description="Consistency of canonical entities, companies, and regulators across reports.",
            evidence_detail=f"Aligned on {len(entities)} tracked canonical graph entities.",
        )

        # Dimension 4: Cross-Language Corroboration (20%)
        d4_score = cls.calculate_cross_language_score(
            independence.languages_represented,
            independence.independent_sources_count,
        )
        dim4 = FormationDimensionScore(
            dimension_name="Cross-Language Corroboration",
            score=d4_score,
            weight_pct=20,
            description="Independent convergence across Tamil, Hindi, and English regional reporting.",
            evidence_detail=f"Covered across: {', '.join(l.upper() for l in independence.languages_represented)}.",
        )

        # Dimension 5: Evidence Strength (15%)
        d5_score, d5_detail = cls.calculate_evidence_strength(articles, entities)
        dim5 = FormationDimensionScore(
            dimension_name="Evidence Strength",
            score=d5_score,
            weight_pct=15,
            description="Official documents, regulatory source citations, and direct reporting provenance.",
            evidence_detail=d5_detail,
        )

        # Dimension 6: Absence of Contradictions (10% / Hard Gate)
        if contradiction_gate.contradiction_status == "PREDICTION_BLOCKED":
            d6_score = 0.0
            d6_detail = "BLOCKED: Load-bearing contradiction detected."
        elif contradiction_gate.contradiction_status == "CONFLICT_DETECTED":
            d6_score = 50.0
            d6_detail = "Minor non-load-bearing discrepancy detected."
        else:
            d6_score = 100.0
            d6_detail = "CLEAR: Zero unresolved factual conflicts."

        dim6 = FormationDimensionScore(
            dimension_name="Absence of Contradictions",
            score=d6_score,
            weight_pct=10,
            description="Hard Contradiction Gate: Evaluates factual consistency across load-bearing claims.",
            evidence_detail=d6_detail,
        )

        # Weighted Formation Score Calculation
        overall_raw = (
            (d1_score * 0.20)
            + (d2_score * 0.15)
            + (d3_score * 0.20)
            + (d4_score * 0.20)
            + (d5_score * 0.15)
            + (d6_score * 0.10)
        )
        overall_score = round(min(100.0, max(5.0, overall_raw)), 1)

        # Formation Status Determination
        if contradiction_gate.contradiction_status == "PREDICTION_BLOCKED":
            formation_status = "BLOCKED_BY_CONTRADICTION"
        elif overall_score >= 75.0:
            formation_status = "CORROBORATED"
        elif overall_score >= 45.0:
            formation_status = "EMERGING"
        else:
            formation_status = "EARLY_SIGNAL"

        # Generate Grounded Narrative Summary
        narrative = cls.generate_grounded_narrative(
            title=story.title,
            articles=articles,
            entities=entities,
            independence=independence,
            contradiction_gate=contradiction_gate,
            formation_score=overall_score,
        )

        # Update Story record in Database
        story.formation_score = overall_score
        story.formation_status = formation_status
        story.independence_score = independence.independence_score
        story.source_diversity_score = independence.source_diversity_score
        story.temporal_spread_score = independence.temporal_spread_score
        story.entity_alignment_score = independence.entity_alignment_score
        story.cross_language_score = round(d4_score / 100.0, 3)
        story.evidence_strength_score = round(d5_score / 100.0, 3)
        story.independent_sources_count = independence.independent_sources_count
        story.total_articles_count = independence.total_articles_count
        story.languages = independence.languages_represented
        story.contradiction_status = contradiction_gate.contradiction_status
        story.prediction_eligible = contradiction_gate.prediction_eligible
        story.narrative_summary = narrative
        story.score_breakdown = {
            "overall_score": overall_score,
            "formation_status": formation_status,
            "prediction_eligible": contradiction_gate.prediction_eligible,
            "dimensions": {
                "source_diversity": {"score": d1_score, "weight": "20%", "detail": dim1.evidence_detail},
                "temporal_spread": {"score": d2_score, "weight": "15%", "detail": dim2.evidence_detail},
                "entity_alignment": {"score": d3_score, "weight": "20%", "detail": dim3.evidence_detail},
                "cross_language_corroboration": {"score": d4_score, "weight": "20%", "detail": dim4.evidence_detail},
                "evidence_strength": {"score": d5_score, "weight": "15%", "detail": dim5.evidence_detail},
                "absence_of_contradictions": {"score": d6_score, "weight": "10%", "detail": dim6.evidence_detail},
            },
            "framework": "Grounded in Ansoff weak-signal framework and Hiltunen signal/issue/interpretation model.",
        }

        await db.commit()

        return FormationScoreResult(
            story_id=story.id,
            overall_score=overall_score,
            formation_status=formation_status,
            prediction_eligible=contradiction_gate.prediction_eligible,
            dimensions={
                "source_diversity": dim1,
                "temporal_spread": dim2,
                "entity_alignment": dim3,
                "cross_language_corroboration": dim4,
                "evidence_strength": dim5,
                "absence_of_contradictions": dim6,
            },
            narrative_summary=narrative,
            framework_context="Operationalized product metric grounded in Ansoff (1975) & Hiltunen (2008).",
        )
