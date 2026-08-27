import logging
from app.agents.base import BaseAgent
from app.schemas.agent import (
    NarrativeFormationInput,
    NarrativeFormationOutput,
    FormationDimensionBreakdown,
)

logger = logging.getLogger(__name__)


class NarrativeFormationAgent(BaseAgent[NarrativeFormationInput, NarrativeFormationOutput]):
    """
    Agent 6 — Narrative & Formation (Core Differentiator)
    Purpose: Computes the explainable Story Formation Score with a visible 6-dimension breakdown,
    grounded in Ansoff's weak-signal and Hiltunen's signal/issue frameworks.
    Phase 0: Foundation & typed interface.
    """
    agent_id = 6
    agent_name = "Narrative & Formation Agent"
    description = "Tracks narrative evolution and calculates the multi-dimensional Story Formation Score."

    async def process(self, input_data: NarrativeFormationInput) -> NarrativeFormationOutput:
        logger.info(f"[{self.agent_name}] Computing formation score for story: {input_data.story_id}")

        breakdown = FormationDimensionBreakdown(
            source_diversity=0.88,
            temporal_spread=0.79,
            entity_alignment=0.92,
            cross_language_corroboration=0.95,
            evidence_strength=0.85,
            absence_of_contradictions=1.0 if not input_data.independence_data.has_load_bearing_contradiction else 0.0,
        )

        formation_score = sum([
            breakdown.source_diversity * 0.20,
            breakdown.temporal_spread * 0.15,
            breakdown.entity_alignment * 0.20,
            breakdown.cross_language_corroboration * 0.20,
            breakdown.evidence_strength * 0.15,
            breakdown.absence_of_contradictions * 0.10,
        ])

        return NarrativeFormationOutput(
            story_id=input_data.story_id,
            narrative_summary="A government inspection involving Company X appears to be developing into a broader regulatory compliance story across Tamil, Hindi, and English regional coverage.",
            formation_score=round(formation_score, 3),
            dimension_breakdown=breakdown,
            framework_citation="Ansoff Weak-Signal Theory (1975) & Hiltunen 3D Signal Model (2008)",
            is_forming=formation_score >= 0.70,
        )
