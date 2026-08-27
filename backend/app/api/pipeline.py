from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.article import Article
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity, Event, GraphEdge
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert
from app.agents.context import ContextAgent
from app.agents.story_clustering import StoryClusteringAgent
from app.agents.independence import IndependenceAgent
from app.agents.formation import NarrativeFormationAgent
from app.agents.prediction import PredictionAgent
from app.agents.evidence import EvidenceInvestigationAgent
from app.agents.alert_orchestrator import AlertOrchestratorAgent
from app.schemas.agent import (
    ContextInput,
    DiscoveredCandidate,
    StoryClusteringInput,
    IndependenceInput,
    NarrativeFormationInput,
    PredictionInput,
    EvidenceInvestigationInput,
    AlertOrchestratorInput,
)
from app.services.clustering_service import StoryClusteringService
from app.services.embedding_service import MultilingualEmbeddingService
from app.services.independence_service import IndependenceService
from app.services.contradiction_service import ContradictionService
from app.services.formation_service import StoryFormationService
from app.services.prediction_service import PredictionService
from app.services.evidence_service import EvidenceService
from app.services.alert_service import AlertOrchestratorService
from app.services.gdelt_service import GdeltIngestionService
from app.services.rss_service import RssIngestionService

router = APIRouter(prefix="/pipeline", tags=["Intelligence Pipeline Execution"])


class PipelineRunResponse(BaseModel):
    status: str = "success"
    articles_processed: int
    entities_extracted: int
    events_extracted: int
    stories_created: int
    languages_covered: List[str]
    executed_at: datetime


class Phase3RunResponse(BaseModel):
    status: str = "success"
    stories_analyzed_count: int
    stories_corroborated_count: int
    stories_blocked_by_contradiction_count: int
    total_contradictions_detected: int
    executed_at: datetime


class Phase4RunResponse(BaseModel):
    status: str = "success"
    stories_evaluated_count: int
    predictions_generated_count: int
    predictions_blocked_count: int
    evidence_chains_built_count: int
    active_alerts_emitted_count: int
    blocked_alerts_count: int
    executed_at: datetime


@router.post("/run-phase2", response_model=PipelineRunResponse, summary="Execute Phase 2 Context & Clustering Pipeline")
async def run_phase2_pipeline(
    watchlist_keywords: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
) -> PipelineRunResponse:
    art_res = await db.execute(select(Article).order_by(Article.published_at.desc()))
    articles = art_res.scalars().all()

    if not articles:
        return PipelineRunResponse(
            status="empty_pipeline",
            articles_processed=0,
            entities_extracted=0,
            events_extracted=0,
            stories_created=0,
            languages_covered=[],
            executed_at=datetime.now(timezone.utc),
        )

    candidates = [
        DiscoveredCandidate(
            title=a.title,
            url=a.url,
            source_name=a.attribution_text,
            language=a.language or "en",
            published_at=a.published_at,
            excerpt=a.excerpt,
        )
        for a in articles
    ]

    context_agent = ContextAgent()
    context_input = ContextInput(
        raw_articles=candidates,
        watchlist_definitions={"keywords": watchlist_keywords or ["Company X", "Tamil Nadu", "Pollution"]},
        languages=["en", "ta", "hi"],
    )
    await context_agent.process(context_input, db=db)

    embedder = MultilingualEmbeddingService()
    for a in articles:
        if a.embedding is None:
            a.embedding = embedder.embed_text(f"{a.title} {a.excerpt}")
    await db.commit()

    created_stories = await StoryClusteringService.cluster_articles(db=db, articles=articles, min_cluster_size=2)

    ent_count_res = await db.execute(select(Entity))
    total_entities = len(ent_count_res.scalars().all())

    ev_count_res = await db.execute(select(Event))
    total_events = len(ev_count_res.scalars().all())

    languages = list(set(a.language for a in articles if a.language))

    return PipelineRunResponse(
        status="success",
        articles_processed=len(articles),
        entities_extracted=total_entities,
        events_extracted=total_events,
        stories_created=len(created_stories),
        languages_covered=languages,
        executed_at=datetime.now(timezone.utc),
    )


@router.post("/run-phase3", response_model=Phase3RunResponse, summary="Execute Phase 3 Independence, Contradictions & Formation Pipeline")
async def run_phase3_pipeline(db: AsyncSession = Depends(get_db)) -> Phase3RunResponse:
    res_stories = await db.execute(select(Story).order_by(Story.created_at.desc()))
    stories = res_stories.scalars().all()

    corroborated_count = 0
    blocked_count = 0
    total_contradictions = 0

    for story in stories:
        art_res = await db.execute(
            select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
                story_articles.c.story_id == story.id
            )
        )
        articles = art_res.scalars().all()

        res_ent = await db.execute(
            select(Entity).join(story_entities, story_entities.c.entity_id == Entity.id).where(
                story_entities.c.story_id == story.id
            )
        )
        entities = res_ent.scalars().all()

        indep_res = await IndependenceService.analyze_story_independence(
            db=db,
            story_id=story.id,
            articles=articles,
            entities=entities,
        )

        gate_res = await ContradictionService.evaluate_contradiction_gate(
            db=db,
            story_id=story.id,
            articles=articles,
        )

        total_contradictions += len(gate_res.contradictions)
        if gate_res.contradiction_status == "PREDICTION_BLOCKED":
            blocked_count += 1

        formation_res = await StoryFormationService.compute_story_formation(
            db=db,
            story=story,
            articles=articles,
            entities=entities,
            independence=indep_res,
            contradiction_gate=gate_res,
        )

        if formation_res.formation_status == "CORROBORATED":
            corroborated_count += 1

    return Phase3RunResponse(
        status="success",
        stories_analyzed_count=len(stories),
        stories_corroborated_count=corroborated_count,
        stories_blocked_by_contradiction_count=blocked_count,
        total_contradictions_detected=total_contradictions,
        executed_at=datetime.now(timezone.utc),
    )


@router.post("/run-phase4", response_model=Phase4RunResponse, summary="Execute Phase 4 Prediction, Evidence & Alert Orchestration Pipeline")
async def run_phase4_pipeline(db: AsyncSession = Depends(get_db)) -> Phase4RunResponse:
    """
    Executes the Phase 4 Intelligence pipeline across all candidate stories:
    1. Agent 7 (Trajectory & Impact Prediction + Contradiction Gate guard)
    2. Agent 8 (Structured Evidence Chain Assembly)
    3. Agent 9 (Defense-in-depth Gate Checks & Alert Ranking)
    """
    res_stories = await db.execute(select(Story).order_by(Story.created_at.desc()))
    stories = res_stories.scalars().all()

    preds_generated = 0
    preds_blocked = 0
    chains_built = 0
    active_alerts = 0
    blocked_alerts = 0

    for story in stories:
        # Fetch articles
        art_res = await db.execute(
            select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
                story_articles.c.story_id == story.id
            )
        )
        articles = art_res.scalars().all()

        # Fetch entities
        res_ent = await db.execute(
            select(Entity).join(story_entities, story_entities.c.entity_id == Entity.id).where(
                story_entities.c.story_id == story.id
            )
        )
        entities = res_ent.scalars().all()

        # 1. Agent 7: Generate Prediction
        pred_res = await PredictionService.generate_prediction(
            db=db,
            story=story,
            articles=articles,
            entities=entities,
        )
        preds_generated += 1
        if pred_res.prediction_status == "BLOCKED":
            preds_blocked += 1

        # 2. Agent 8: Build Evidence Chain
        chain_res = await EvidenceService.build_evidence_chain(
            db=db,
            story=story,
            articles=articles,
        )
        chains_built += 1

        # Fetch DB models for Agent 9
        res_p = await db.execute(select(Prediction).where(Prediction.story_id == story.id))
        pred_db = res_p.scalars().first()

        res_e = await db.execute(select(EvidenceChain).where(EvidenceChain.story_id == story.id))
        chain_db = res_e.scalars().first()

        # 3. Agent 9: Evaluate Defense-in-Depth Alert Creation
        alert_db = await AlertOrchestratorService.evaluate_and_create_alert(
            db=db,
            story=story,
            prediction=pred_db,
            evidence_chain=chain_db,
            articles=articles,
        )

        if alert_db:
            if alert_db.status == "ACTIVE":
                active_alerts += 1
            elif alert_db.status == "BLOCKED":
                blocked_alerts += 1

    return Phase4RunResponse(
        status="success",
        stories_evaluated_count=len(stories),
        predictions_generated_count=preds_generated,
        predictions_blocked_count=preds_blocked,
        evidence_chains_built_count=chains_built,
        active_alerts_emitted_count=active_alerts,
        blocked_alerts_count=blocked_alerts,
        executed_at=datetime.now(timezone.utc),
    )


class FullPipelineRunResponse(BaseModel):
    status: str = "success"
    gdelt_articles_fetched: int = 0
    gdelt_articles_accepted: int = 0
    rss_articles_fetched: int = 0
    rss_articles_accepted: int = 0
    duplicates_skipped: int = 0
    total_articles_in_db: int = 0
    entities_extracted: int = 0
    events_extracted: int = 0
    stories_formed_count: int = 0
    active_alerts_count: int = 0
    blocked_alerts_count: int = 0
    languages_covered: List[str] = Field(default_factory=list)
    is_live: bool = True
    executed_at: datetime


@router.post("/execute", response_model=FullPipelineRunResponse, summary="Execute End-to-End Live Ingestion & Intelligence Pipeline")
@router.post("/run", response_model=FullPipelineRunResponse, summary="Execute End-to-End Live Ingestion & Intelligence Pipeline (Alias)")
@router.post("/run-all", response_model=FullPipelineRunResponse, summary="Execute End-to-End Live Ingestion & Intelligence Pipeline (Alias)")
async def execute_full_pipeline(
    query_topic: Optional[str] = None,
    watchlist_keywords: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
) -> FullPipelineRunResponse:
    """
    Executes the entire Pre-Headline Intelligence pipeline end-to-end:
    1. Agent 1 Discovery: Live GDELT DOC 2.0 & Multilingual RSS Ingestion
    2. Deduplication & Normalization into Article & Source records
    3. Agent 2 Context: Multilingual Entity & Event Extraction + Graph Expansion
    4. Dense Vector Embeddings + Agent 4 Story Clustering Engine (HDBSCAN)
    5. Agent 3 & 5: Independent Source Detection & Hard Contradiction Gate
    6. Agent 6: Grounded Story Formation Score Calibration (Ansoff weak-signal framework)
    7. Agent 7: Trajectory & Impact Prediction
    8. Agent 8: Traceable Structured Evidence Chain Assembly
    9. Agent 9: Defense-in-depth Gate Checks & Alert Ranking (Urgency × Probability × Impact)
    """
    # 1. Live Ingestion: GDELT DOC 2.0
    gdelt_res = await GdeltIngestionService.ingest_gkg_events(db, query_topic=query_topic)
    gdelt_fetched = gdelt_res.get("total_records", 0)
    gdelt_accepted = gdelt_res.get("new_articles", 0)
    gdelt_dup = gdelt_res.get("duplicates_skipped", 0)

    # 2. Live Ingestion: Configured Multilingual RSS Feeds
    rss_results = await RssIngestionService.ingest_all_configured_feeds(db)
    rss_fetched = sum(r.get("total_items", 0) for r in rss_results)
    rss_accepted = sum(r.get("new_articles", 0) for r in rss_results)
    rss_dup = sum(r.get("duplicates_skipped", 0) for r in rss_results)

    total_dup = gdelt_dup + rss_dup

    # 3. Retrieve all articles in DB
    art_res = await db.execute(select(Article).order_by(Article.published_at.desc()))
    articles = art_res.scalars().all()
    total_articles = len(articles)

    if not articles:
        return FullPipelineRunResponse(
            status="empty_pipeline",
            gdelt_articles_fetched=gdelt_fetched,
            gdelt_articles_accepted=gdelt_accepted,
            rss_articles_fetched=rss_fetched,
            rss_articles_accepted=rss_accepted,
            duplicates_skipped=total_dup,
            total_articles_in_db=0,
            entities_extracted=0,
            events_extracted=0,
            stories_formed_count=0,
            active_alerts_count=0,
            blocked_alerts_count=0,
            languages_covered=[],
            is_live=True,
            executed_at=datetime.now(timezone.utc),
        )

    # 4. Agent 2 Context Extraction & Graph Expansion
    candidates = [
        DiscoveredCandidate(
            title=a.title,
            url=a.url,
            source_name=a.attribution_text,
            language=a.language or "en",
            published_at=a.published_at,
            excerpt=a.excerpt,
        )
        for a in articles
    ]

    context_agent = ContextAgent()
    context_input = ContextInput(
        raw_articles=candidates,
        watchlist_definitions={"keywords": watchlist_keywords or ["Company X", "Tamil Nadu", "Pollution", "Regulatory", "Technology", "Climate"]},
        languages=["en", "ta", "hi"],
    )
    await context_agent.process(context_input, db=db)

    # 5. Multilingual Vector Embeddings
    embedder = MultilingualEmbeddingService()
    for a in articles:
        if a.embedding is None:
            a.embedding = embedder.embed_text(f"{a.title} {a.excerpt}")
    await db.commit()

    # 6. Agent 4 Story Clustering Engine (HDBSCAN with singletons enabled for full coverage)
    created_stories = await StoryClusteringService.cluster_articles(
        db=db,
        articles=articles,
        min_cluster_size=2,
        include_singletons=True,
    )

    # 7. Agent 3, 5, 6: Independence, Contradictions & Formation
    res_stories = await db.execute(select(Story).order_by(Story.created_at.desc()))
    stories = res_stories.scalars().all()

    for story in stories:
        s_art_res = await db.execute(
            select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
                story_articles.c.story_id == story.id
            )
        )
        s_articles = s_art_res.scalars().all()

        s_ent_res = await db.execute(
            select(Entity).join(story_entities, story_entities.c.entity_id == Entity.id).where(
                story_entities.c.story_id == story.id
            )
        )
        s_entities = s_ent_res.scalars().all()

        indep_res = await IndependenceService.analyze_story_independence(
            db=db,
            story_id=story.id,
            articles=s_articles,
            entities=s_entities,
        )

        gate_res = await ContradictionService.evaluate_contradiction_gate(
            db=db,
            story_id=story.id,
            articles=s_articles,
        )

        await StoryFormationService.compute_story_formation(
            db=db,
            story=story,
            articles=s_articles,
            entities=s_entities,
            independence=indep_res,
            contradiction_gate=gate_res,
        )

    # 8. Agent 7, 8, 9: Prediction, Evidence Chains & Alert Orchestration
    active_alerts = 0
    blocked_alerts = 0

    for story in stories:
        s_art_res = await db.execute(
            select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
                story_articles.c.story_id == story.id
            )
        )
        s_articles = s_art_res.scalars().all()

        s_ent_res = await db.execute(
            select(Entity).join(story_entities, story_entities.c.entity_id == Entity.id).where(
                story_entities.c.story_id == story.id
            )
        )
        s_entities = s_ent_res.scalars().all()

        pred_res = await PredictionService.generate_prediction(
            db=db,
            story=story,
            articles=s_articles,
            entities=s_entities,
        )

        chain_res = await EvidenceService.build_evidence_chain(
            db=db,
            story=story,
            articles=s_articles,
        )

        res_p = await db.execute(select(Prediction).where(Prediction.story_id == story.id))
        pred_db = res_p.scalars().first()

        res_e = await db.execute(select(EvidenceChain).where(EvidenceChain.story_id == story.id))
        chain_db = res_e.scalars().first()

        alert_db = await AlertOrchestratorService.evaluate_and_create_alert(
            db=db,
            story=story,
            prediction=pred_db,
            evidence_chain=chain_db,
            articles=s_articles,
        )

        if alert_db:
            if alert_db.status == "ACTIVE":
                active_alerts += 1
            elif alert_db.status == "BLOCKED":
                blocked_alerts += 1

    ent_count_res = await db.execute(select(Entity))
    total_entities = len(ent_count_res.scalars().all())

    ev_count_res = await db.execute(select(Event))
    total_events = len(ev_count_res.scalars().all())

    languages = list(set(a.language for a in articles if a.language))

    return FullPipelineRunResponse(
        status="success",
        gdelt_articles_fetched=gdelt_fetched,
        gdelt_articles_accepted=gdelt_accepted,
        rss_articles_fetched=rss_fetched,
        rss_articles_accepted=rss_accepted,
        duplicates_skipped=total_dup,
        total_articles_in_db=total_articles,
        entities_extracted=total_entities,
        events_extracted=total_events,
        stories_formed_count=len(stories),
        active_alerts_count=active_alerts,
        blocked_alerts_count=blocked_alerts,
        languages_covered=languages,
        is_live=True,
        executed_at=datetime.now(timezone.utc),
    )

