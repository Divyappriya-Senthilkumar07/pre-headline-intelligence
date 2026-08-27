import pytest
from datetime import datetime
from app.agents import (
    DiscoveryAgent,
    ContextAgent,
    ExpansionAgent,
    StoryClusteringAgent,
    IndependenceCorroborationAgent,
    NarrativeFormationAgent,
    PredictionAgent,
    EvidenceInvestigationAgent,
    AlertOrchestratorAgent,
)
from app.schemas.agent import (
    DiscoveryInput,
    ContextInput,
    ExpansionInput,
    StoryClusteringInput,
    IndependenceInput,
    NarrativeFormationInput,
    PredictionInput,
    EvidenceInvestigationInput,
    AlertOrchestratorInput,
    AlertCandidate,
    FormationDimensionBreakdown,
)


@pytest.mark.asyncio
async def test_all_nine_agents_execution_and_contracts():
    """Verify that all 9 intelligence agents can be imported, instantiated, and processed."""
    
    # 1. Agent 1 — Discovery
    agent1 = DiscoveryAgent()
    assert agent1.agent_id == 1
    out1 = await agent1.process(
        DiscoveryInput(
            watchlist_ids=["wl-1"],
            entity_keywords=["Company X"],
            languages=["ta", "hi", "en"],
        )
    )
    assert out1.status == "success"
    assert out1.total_found >= 1

    # 2. Agent 2 — Context
    agent2 = ContextAgent()
    assert agent2.agent_id == 2
    out2 = await agent2.process(
        ContextInput(
            article_id="art-101",
            title="State inspection at Company X facility",
            excerpt="Environmental regulators visit plant premises.",
            tracked_entities=["Company X"],
        )
    )
    assert out2.is_confirmed_relevant is True
    assert len(out2.extracted_entities) >= 1

    # 3. Agent 3 — Expansion
    agent3 = ExpansionAgent()
    assert agent3.agent_id == 3
    out3 = await agent3.process(
        ExpansionInput(
            article_id="art-101",
            confirmed_entity_ids=["Company X"],
            max_hops=2,
        )
    )
    assert len(out3.related_article_ids) > 0
    assert out3.graph_edges_discovered > 0

    # 4. Agent 4 — Story Clustering
    agent4 = StoryClusteringAgent()
    assert agent4.agent_id == 4
    out4 = await agent4.process(
        StoryClusteringInput(candidate_article_ids=["art-101", "art-102", "art-103"])
    )
    assert out4.total_clusters >= 1

    # 5. Agent 5 — Independence & Corroboration
    agent5 = IndependenceCorroborationAgent()
    assert agent5.agent_id == 5
    out5 = await agent5.process(
        IndependenceInput(story_id="story-001", article_ids=["art-101", "art-102", "art-103", "art-104"])
    )
    assert out5.independence_score > 0.5
    assert out5.independent_sources_count == 3  # Correctly identifies 3 independent vs 4 total

    # 6. Agent 6 — Narrative & Formation
    agent6 = NarrativeFormationAgent()
    assert agent6.agent_id == 6
    out6 = await agent6.process(
        NarrativeFormationInput(
            story_id="story-001",
            independence_data=out5,
            timeline_timestamps=[datetime.utcnow()],
        )
    )
    assert out6.formation_score >= 0.70
    assert out6.is_forming is True
    assert "Ansoff" in out6.framework_citation

    # 7. Agent 7 — Prediction
    agent7 = PredictionAgent()
    assert agent7.agent_id == 7
    out7 = await agent7.process(
        PredictionInput(
            story_id="story-001",
            formation_score=out6.formation_score,
            dimension_breakdown=out6.dimension_breakdown,
            has_unresolved_contradictions=False,
        )
    )
    assert out7.probability > 0.0
    assert out7.impact > 0.0
    assert out7.is_halted is False

    # 8. Agent 8 — Evidence & Investigation
    agent8 = EvidenceInvestigationAgent()
    assert agent8.agent_id == 8
    out8 = await agent8.process(
        EvidenceInvestigationInput(
            story_id="story-001",
            query_text="Why is the confidence high for this story?",
        )
    )
    assert len(out8.evidence_chain) == 3
    assert out8.copilot_answer is not None
    assert len(out8.grounded_citations) > 0

    # 9. Agent 9 — Alert Orchestrator & Contradiction Gate
    agent9 = AlertOrchestratorAgent()
    assert agent9.agent_id == 9
    
    # Candidate A: Clean story -> should emit alert
    clean_candidate = AlertCandidate(
        story_id="story-001",
        title="Company X Regulatory Inspection",
        formation_score=0.88,
        probability=0.85,
        impact=0.88,
        has_load_bearing_contradiction=False,
        independent_sources_count=3,
        languages=["ta", "hi", "en"],
    )
    
    # Candidate B: Load-bearing contradiction -> should trigger Contradiction Gate and HALT
    contradicted_candidate = AlertCandidate(
        story_id="story-002",
        title="Conflicting Regulatory Permit Status",
        formation_score=0.85,
        probability=0.80,
        impact=0.90,
        has_load_bearing_contradiction=True,
        independent_sources_count=2,
        languages=["en"],
    )

    out9 = await agent9.process(
        AlertOrchestratorInput(
            candidate_stories=[clean_candidate, contradicted_candidate],
            min_rank_threshold=0.2,
        )
    )

    # Clean story must emit alert
    assert len(out9.emitted_alerts) == 1
    assert out9.emitted_alerts[0].story_id == "story-001"
    
    # Contradicted story MUST be halted by Contradiction Gate
    assert len(out9.halted_predictions) == 1
    assert out9.halted_predictions[0].story_id == "story-002"
    assert "Contradiction Gate" in out9.halted_predictions[0].reason
