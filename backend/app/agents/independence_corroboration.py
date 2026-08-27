import logging
from app.agents.base import BaseAgent
from app.schemas.agent import (
    IndependenceInput,
    IndependenceOutput,
    SourceIndependenceBreakdown,
    ContradictionItem,
)

logger = logging.getLogger(__name__)


class IndependenceCorroborationAgent(BaseAgent[IndependenceInput, IndependenceOutput]):
    """
    Agent 5 — Independence & Corroboration (Core Differentiator)
    Purpose: Distinguishes syndicated copies from genuinely independent corroboration,
    computes the Independence Score across 3 sub-scores (Source Diversity, Temporal Spread, Entity Alignment),
    and flags direct contradictions on load-bearing claims.
    Phase 0: Foundation & typed interface.
    """
    agent_id = 5
    agent_name = "Independence & Corroboration Agent"
    description = "Evaluates genuine independence vs syndication and detects conflicting load-bearing claims."

    async def process(self, input_data: IndependenceInput) -> IndependenceOutput:
        logger.info(f"[{self.agent_name}] Scoring independence for story: {input_data.story_id} ({len(input_data.article_ids)} articles)")

        # In Phase 0 placeholder, mock 3 independent sources out of 4 articles
        breakdown = [
            SourceIndependenceBreakdown(source_name="Tamil Regional Daily", is_original=True, individual_independence_score=0.9),
            SourceIndependenceBreakdown(source_name="State Gazette / Govt Document", is_original=True, individual_independence_score=1.0),
            SourceIndependenceBreakdown(source_name="National Wire Service", is_original=False, syndication_origin="Tamil Regional Daily", individual_independence_score=0.2),
            SourceIndependenceBreakdown(source_name="Independent Hindi Portal", is_original=True, individual_independence_score=0.85),
        ]

        return IndependenceOutput(
            story_id=input_data.story_id,
            independence_score=0.88,
            independent_sources_count=3,
            total_articles_count=len(input_data.article_ids) or 4,
            source_breakdown=breakdown,
            detected_contradictions=[],
            has_load_bearing_contradiction=False,
        )
