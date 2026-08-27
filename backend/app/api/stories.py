from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, asc
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.story import Story, story_articles, story_entities
from app.models.article import Article
from app.models.source import Source
from app.models.graph import Entity, Event
from app.models.claim import Claim
from app.models.contradiction import Contradiction
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert
from app.models.story_note import StoryNote
from app.models.media import Media, MediaExtraction

from app.services.independence_service import IndependenceService
from app.services.contradiction_service import ContradictionService
from app.services.formation_service import StoryFormationService
from app.services.prediction_service import PredictionService
from app.services.evidence_service import EvidenceService
from app.services.alert_service import AlertOrchestratorService, AlertItemDetail

router = APIRouter(prefix="/stories", tags=["Story Formation Intelligence"])


# -----------------------------------------------------------------------------
# Pydantic Response & Request Schemas
# -----------------------------------------------------------------------------
class StoryArticleItem(BaseModel):
    id: str
    title: str
    source_name: str
    domain: str
    url: str
    language: str
    published_at: datetime
    excerpt: str
    relationship_type: str = "INDEPENDENT"
    is_original: bool = True
    syndication_origin: Optional[str] = None


class StoryEntityItem(BaseModel):
    id: str
    name: str
    canonical_name: str
    entity_type: str


class ContradictionDetailItem(BaseModel):
    id: str
    story_id: str
    claim_a_id: str
    claim_b_id: str
    claim_a_statement: str
    claim_b_statement: str
    claim_a_source: str
    claim_b_source: str
    is_load_bearing: bool
    status: str
    severity: str
    description: str
    halted_prediction: bool
    detected_at: Optional[str] = None


class PredictionDetailItem(BaseModel):
    id: str
    formation_probability: float
    impact_score: float
    impact_level: str
    current_stage: str
    predicted_next_stage: str
    trajectory_confidence: float
    trajectory_reasoning: str
    prediction_status: str
    blocked_reason: Optional[str] = None
    historical_support_level: str = "LIMITED_HISTORICAL_DATA"
    explanation: str


class EvidenceChainItemResponse(BaseModel):
    item_id: str
    step_order: int
    source_name: str
    domain: str
    claim_statement: str
    evidence_type: str
    evidence_excerpt: str
    corroborating_sources: List[str] = Field(default_factory=list)
    confidence_contribution: float


class EvidenceChainDetailItem(BaseModel):
    id: str
    chain_status: str
    confidence_score: float
    items: List[EvidenceChainItemResponse] = Field(default_factory=list)
    has_sufficient_evidence: bool


class StoryNoteResponse(BaseModel):
    id: str
    story_id: str
    user_id: str
    note: str
    created_at: datetime
    updated_at: datetime


class CreateStoryNoteRequest(BaseModel):
    note: str = Field(..., min_length=2, description="Analyst observation or investigation note")
    user_id: Optional[str] = "analyst-default"


class StoryStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="INVESTIGATING | ACKNOWLEDGED | DISMISSED | RESOLVED")
    notes: Optional[str] = None


class StoryTimelineItem(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    title: str
    source_name: str
    language: str
    claim_statement: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None


class StoryListItem(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    status: str
    formation_status: str
    formation_score: float
    article_count: int
    independent_sources_count: int
    independence_score: float
    contradiction_status: str
    prediction_eligible: bool
    languages: List[str]
    primary_entities: List[str]
    created_at: datetime


class StoryDetailResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    status: str
    formation_status: str
    formation_score: float
    narrative_summary: Optional[str] = None
    article_count: int
    candidate_sources_count: int
    independent_sources_count: int
    independence_score: float
    source_diversity_score: float
    temporal_spread_score: float
    entity_alignment_score: float
    cross_language_score: float
    evidence_strength_score: float
    contradiction_status: str
    prediction_eligible: bool
    created_at: datetime
    languages: List[str] = Field(default_factory=list)
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    articles: List[StoryArticleItem] = Field(default_factory=list)
    entities: List[StoryEntityItem] = Field(default_factory=list)
    contradictions: List[ContradictionDetailItem] = Field(default_factory=list)
    prediction: Optional[PredictionDetailItem] = None
    evidence_chain: Optional[EvidenceChainDetailItem] = None
    notes: List[StoryNoteResponse] = Field(default_factory=list)
    alert_status: Optional[str] = "ACTIVE"


class ResolveContradictionRequest(BaseModel):
    resolution_notes: str = "Resolved by intelligence analyst after verifying official register."


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/emerging", response_model=List[AlertItemDetail], summary="Get Ranked Active Emerging Intelligence Feed with Filtering")
async def get_emerging_stories_feed(
    search: Optional[str] = Query(None, description="Search keyword across title, entities, or summary"),
    min_formation_score: Optional[float] = Query(None, description="Minimum formation score (0-100)"),
    min_probability: Optional[float] = Query(None, description="Minimum probability (0.0-1.0)"),
    min_impact: Optional[float] = Query(None, description="Minimum impact (0.0-1.0)"),
    min_urgency: Optional[float] = Query(None, description="Minimum urgency (0.0-1.0)"),
    trajectory: Optional[str] = Query(None, description="Filter by trajectory stage (EARLY, REGIONAL, NATIONAL, MAINSTREAM)"),
    language: Optional[str] = Query(None, description="Filter by language code (ta, hi, en)"),
    contradiction_status: Optional[str] = Query(None, description="CLEAR | PREDICTION_BLOCKED | RESOLVED"),
    evidence_only: Optional[bool] = Query(None, description="Only stories with verified evidence chains"),
    sort_by: Optional[str] = Query("ranking_score", description="ranking_score | formation_score | probability | impact | urgency | latest_update | independent_sources"),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> List[AlertItemDetail]:
    """
    Returns ranked active alerts and emerging stories with analyst filtering and explainable ranking.
    """
    # 1. Fetch raw alerts
    alerts_query = select(Alert)

    if contradiction_status:
        alerts_query = alerts_query.where(Alert.contradiction_status == contradiction_status.upper())

    if min_formation_score is not None:
        alerts_query = alerts_query.where(Alert.formation_score >= min_formation_score)

    if min_probability is not None:
        alerts_query = alerts_query.where(Alert.probability >= min_probability)

    if min_impact is not None:
        alerts_query = alerts_query.where(Alert.impact >= min_impact)

    if min_urgency is not None:
        alerts_query = alerts_query.where(Alert.urgency >= min_urgency)

    if evidence_only is True:
        alerts_query = alerts_query.where(Alert.evidence_available == True)

    # Sorting
    if sort_by == "formation_score":
        alerts_query = alerts_query.order_by(Alert.formation_score.desc())
    elif sort_by == "probability":
        alerts_query = alerts_query.order_by(Alert.probability.desc())
    elif sort_by == "impact":
        alerts_query = alerts_query.order_by(Alert.impact.desc())
    elif sort_by == "urgency":
        alerts_query = alerts_query.order_by(Alert.urgency.desc())
    elif sort_by == "independent_sources":
        alerts_query = alerts_query.order_by(Alert.independent_source_count.desc())
    elif sort_by == "latest_update":
        alerts_query = alerts_query.order_by(Alert.created_at.desc())
    else:  # default: ranking_score
        alerts_query = alerts_query.order_by(Alert.ranking_score.desc(), Alert.created_at.desc())

    alerts_query = alerts_query.offset(offset).limit(limit)

    res = await db.execute(alerts_query)
    alerts = res.scalars().all()

    output: List[AlertItemDetail] = []
    for a in alerts:
        # Search text match filter
        if search:
            s_low = search.strip().lower()
            text_match = (
                s_low in (a.title or "").lower() or
                s_low in (a.headline_in_progress or "").lower() or
                s_low in (a.why_it_matters or "").lower() or
                any(s_low in l.lower() for l in (a.languages or []))
            )
            if not text_match:
                continue

        if language and language.lower() not in [l.lower() for l in (a.languages or [])]:
            continue

        output.append(
            AlertItemDetail(
                id=a.id,
                story_id=a.story_id,
                alert_type=a.alert_type,
                headline_in_progress=a.headline_in_progress or a.title,
                why_it_matters=a.why_it_matters or "Insufficient evidence for a reliable explanation.",
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


@router.get("", response_model=List[StoryListItem], summary="List Candidate Story Clusters with Intelligence Metrics")
async def list_stories(
    search: Optional[str] = Query(None, description="Search keyword across title or narrative summary"),
    min_formation_score: Optional[float] = Query(None, description="Minimum formation score"),
    min_independent_sources: Optional[int] = Query(None, description="Minimum independent sources"),
    language: Optional[str] = Query(None, description="Language filter (ta, hi, en)"),
    contradiction_status: Optional[str] = Query(None, description="CLEAR | PREDICTION_BLOCKED | RESOLVED"),
    sort_by: Optional[str] = Query("formation_score", description="formation_score | independent_sources | created_at"),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> List[StoryListItem]:
    query = select(Story)

    if contradiction_status:
        query = query.where(Story.contradiction_status == contradiction_status.upper())

    if min_formation_score is not None:
        query = query.where(Story.formation_score >= min_formation_score)

    if min_independent_sources is not None:
        query = query.where(Story.independent_sources_count >= min_independent_sources)

    if search:
        s_term = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                Story.title.ilike(s_term),
                Story.why_it_matters.ilike(s_term),
                Story.narrative_summary.ilike(s_term),
            )
        )

    if sort_by == "independent_sources":
        query = query.order_by(Story.independent_sources_count.desc())
    elif sort_by == "created_at":
        query = query.order_by(Story.created_at.desc())
    else:  # default formation_score
        query = query.order_by(Story.formation_score.desc(), Story.created_at.desc())

    query = query.offset(offset).limit(limit)

    res = await db.execute(query)
    stories = res.scalars().all()

    output = []
    for s in stories:
        meta = s.metadata_json or {}
        art_res = await db.execute(
            select(story_articles.c.article_id).where(story_articles.c.story_id == s.id)
        )
        art_ids = art_res.scalars().all()

        langs = s.languages or meta.get("languages", ["en"])
        if language and language.lower() not in [l.lower() for l in langs]:
            continue

        output.append(
            StoryListItem(
                id=s.id,
                title=s.title,
                summary=s.why_it_matters,
                why_it_matters=s.why_it_matters or s.narrative_summary or "Insufficient evidence for a reliable explanation.",
                status=s.status,
                formation_status=s.formation_status or "EMERGING",
                formation_score=s.formation_score or 0.0,
                article_count=len(art_ids) or s.total_articles_count or meta.get("cluster_size", 0),
                independent_sources_count=s.independent_sources_count or 1,
                independence_score=s.independence_score or 0.0,
                contradiction_status=s.contradiction_status or "CLEAR",
                prediction_eligible=s.prediction_eligible if s.prediction_eligible is not None else True,
                languages=langs,
                primary_entities=meta.get("entity_names", []),
                created_at=s.created_at,
            )
        )
    return output


@router.get("/{story_id}", response_model=StoryDetailResponse, summary="Get Full Story Intelligence Workspace Details")
async def get_story_detail(story_id: str, db: AsyncSession = Depends(get_db)) -> StoryDetailResponse:
    res = await db.execute(select(Story).where(Story.id == story_id))
    story = res.scalars().first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Story {story_id} not found.")

    # 1. Fetch connected articles
    art_res = await db.execute(
        select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
            story_articles.c.story_id == story_id
        )
    )
    articles_db = art_res.scalars().all()

    # 2. Fetch connected entities
    ent_res = await db.execute(
        select(Entity).join(story_entities, story_entities.c.entity_id == Entity.id).where(
            story_entities.c.story_id == story_id
        )
    )
    entities_db = ent_res.scalars().all()

    # 3. Fetch Independence Analysis
    indep_res = await IndependenceService.analyze_story_independence(
        db=db,
        story_id=story_id,
        articles=articles_db,
        entities=entities_db,
    )

    # 4. Fetch Contradiction Gate
    gate_res = await ContradictionService.evaluate_contradiction_gate(
        db=db,
        story_id=story_id,
        articles=articles_db,
    )

    # 5. Compute Formation Score if needed
    if not story.score_breakdown or not story.narrative_summary:
        await StoryFormationService.compute_story_formation(
            db=db,
            story=story,
            articles=articles_db,
            entities=entities_db,
            independence=indep_res,
            contradiction_gate=gate_res,
        )

    # 6. Fetch Prediction
    pred_res = await PredictionService.generate_prediction(
        db=db,
        story=story,
        articles=articles_db,
        entities=entities_db,
        contradiction_gate=gate_res,
    )

    # 7. Fetch Evidence Chain
    chain_res = await EvidenceService.build_evidence_chain(
        db=db,
        story=story,
        articles=articles_db,
    )

    # 8. Fetch Analyst Notes
    notes_res = await db.execute(select(StoryNote).where(StoryNote.story_id == story_id).order_by(StoryNote.created_at.desc()))
    notes_db = notes_res.scalars().all()

    # Build relationship lookup
    rel_map = {r.article_id: r for r in indep_res.source_relationships}

    articles_out = [
        StoryArticleItem(
            id=a.id,
            title=a.title,
            source_name=a.attribution_text,
            domain=(rel_map[a.id].domain if a.id in rel_map else (a.url.split("/")[2] if "://" in a.url else "source.org")),
            url=a.url,
            language=a.language or "en",
            published_at=a.published_at,
            excerpt=a.excerpt,
            relationship_type=(rel_map[a.id].relationship_type if a.id in rel_map else "INDEPENDENT"),
            is_original=(rel_map[a.id].relationship_type in ["ORIGINAL", "INDEPENDENT"] if a.id in rel_map else True),
            syndication_origin=(rel_map[a.id].original_source_id if a.id in rel_map else None),
        )
        for a in articles_db
    ]

    entities_out = [
        StoryEntityItem(
            id=e.id,
            name=e.name,
            canonical_name=e.canonical_name,
            entity_type=e.entity_type,
        )
        for e in entities_db
    ]

    claim_ids = [c.claim_a_id for c in gate_res.contradictions] + [c.claim_b_id for c in gate_res.contradictions]
    claims_map: Dict[str, Claim] = {}
    if claim_ids:
        cl_res = await db.execute(select(Claim).where(Claim.id.in_(claim_ids)))
        for cl in cl_res.scalars().all():
            claims_map[cl.id] = cl

    contradictions_out = [
        ContradictionDetailItem(
            id=c.id,
            story_id=c.story_id,
            claim_a_id=c.claim_a_id,
            claim_b_id=c.claim_b_id,
            claim_a_statement=claims_map.get(c.claim_a_id).statement if c.claim_a_id in claims_map else c.conflict_metadata.get("claim_a_statement", "Claim A"),
            claim_b_statement=claims_map.get(c.claim_b_id).statement if c.claim_b_id in claims_map else c.conflict_metadata.get("claim_b_statement", "Claim B"),
            claim_a_source=claims_map.get(c.claim_a_id).metadata_json.get("source", "Source A") if c.claim_a_id in claims_map else "Source A",
            claim_b_source=claims_map.get(c.claim_b_id).metadata_json.get("source", "Source B") if c.claim_b_id in claims_map else "Source B",
            is_load_bearing=c.is_load_bearing,
            status=c.status,
            severity=c.severity,
            description=c.description,
            halted_prediction=c.halted_prediction,
            detected_at=c.conflict_metadata.get("detected_at"),
        )
        for c in gate_res.contradictions
    ]

    prediction_out = PredictionDetailItem(
        id=pred_res.id,
        formation_probability=pred_res.formation_probability,
        impact_score=pred_res.impact_score,
        impact_level=pred_res.impact_level,
        current_stage=pred_res.current_stage,
        predicted_next_stage=pred_res.predicted_next_stage,
        trajectory_confidence=pred_res.trajectory_confidence,
        trajectory_reasoning=pred_res.trajectory_reasoning,
        prediction_status=pred_res.prediction_status,
        blocked_reason=pred_res.blocked_reason,
        historical_support_level=pred_res.historical_pattern.support_level,
        explanation=pred_res.explanation,
    )

    evidence_chain_out = EvidenceChainDetailItem(
        id=chain_res.id,
        chain_status=chain_res.chain_status,
        confidence_score=chain_res.confidence_score,
        has_sufficient_evidence=chain_res.has_sufficient_evidence,
        items=[
            EvidenceChainItemResponse(
                item_id=it.item_id,
                step_order=it.step_order,
                source_name=it.source_name,
                domain=it.domain,
                claim_statement=it.claim_statement,
                evidence_type=it.evidence_type,
                evidence_excerpt=it.evidence_excerpt,
                corroborating_sources=it.corroborating_sources,
                confidence_contribution=it.confidence_contribution,
            )
            for it in chain_res.items
        ],
    )

    notes_out = [
        StoryNoteResponse(
            id=n.id,
            story_id=n.story_id,
            user_id=n.user_id,
            note=n.note,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in notes_db
    ]

    res_alt = await db.execute(select(Alert.status).where(Alert.story_id == story_id))
    alt_status = res_alt.scalars().first() or ("BLOCKED" if gate_res.contradiction_status == "PREDICTION_BLOCKED" else "ACTIVE")

    why_matters = story.why_it_matters or story.narrative_summary or "Insufficient evidence for a reliable explanation."

    return StoryDetailResponse(
        id=story.id,
        title=story.title,
        summary=story.why_it_matters,
        why_it_matters=why_matters,
        status=story.status,
        formation_status=story.formation_status or "EMERGING",
        formation_score=story.formation_score or 0.0,
        narrative_summary=story.narrative_summary,
        article_count=len(articles_db),
        candidate_sources_count=indep_res.candidate_sources_count,
        independent_sources_count=story.independent_sources_count or indep_res.independent_sources_count,
        independence_score=story.independence_score or indep_res.independence_score,
        source_diversity_score=story.source_diversity_score or indep_res.source_diversity_score,
        temporal_spread_score=story.temporal_spread_score or indep_res.temporal_spread_score,
        entity_alignment_score=story.entity_alignment_score or indep_res.entity_alignment_score,
        cross_language_score=story.cross_language_score or 0.0,
        evidence_strength_score=story.evidence_strength_score or 0.0,
        contradiction_status=story.contradiction_status or gate_res.contradiction_status,
        prediction_eligible=story.prediction_eligible if story.prediction_eligible is not None else gate_res.prediction_eligible,
        created_at=story.created_at,
        languages=story.languages or indep_res.languages_represented,
        score_breakdown=story.score_breakdown or {},
        articles=articles_out,
        entities=entities_out,
        contradictions=contradictions_out,
        prediction=prediction_out,
        evidence_chain=evidence_chain_out,
        notes=notes_out,
        alert_status=alt_status,
    )


# -----------------------------------------------------------------------------
# Story Notes Endpoints
# -----------------------------------------------------------------------------
@router.get("/{story_id}/notes", response_model=List[StoryNoteResponse], summary="Get Analyst Notes for a Story")
async def get_story_notes(story_id: str, db: AsyncSession = Depends(get_db)) -> List[StoryNoteResponse]:
    res = await db.execute(select(StoryNote).where(StoryNote.story_id == story_id).order_by(StoryNote.created_at.desc()))
    notes = res.scalars().all()
    return [
        StoryNoteResponse(
            id=n.id,
            story_id=n.story_id,
            user_id=n.user_id,
            note=n.note,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in notes
    ]


@router.post("/{story_id}/notes", response_model=StoryNoteResponse, status_code=status.HTTP_201_CREATED, summary="Add Analyst Note to Story")
async def add_story_note(
    story_id: str,
    payload: CreateStoryNoteRequest,
    db: AsyncSession = Depends(get_db),
) -> StoryNoteResponse:
    res_s = await db.execute(select(Story).where(Story.id == story_id))
    story = res_s.scalars().first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Story {story_id} not found.")

    note = StoryNote(
        story_id=story_id,
        user_id=payload.user_id or "analyst-default",
        note=payload.note,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return StoryNoteResponse(
        id=note.id,
        story_id=note.story_id,
        user_id=note.user_id,
        note=note.note,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.delete("/{story_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Story Note")
async def delete_story_note(
    story_id: str,
    note_id: str,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(StoryNote).where(StoryNote.id == note_id, StoryNote.story_id == story_id))
    note = res.scalars().first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Note {note_id} not found on story {story_id}.")

    await db.delete(note)
    await db.commit()
    return None


@router.post("/{story_id}/status", summary="Update Analyst Investigation Status on Story")
async def update_story_status(
    story_id: str,
    body: StoryStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Story).where(Story.id == story_id))
    story = res.scalars().first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Story {story_id} not found.")

    valid_statuses = ["EMERGING", "INVESTIGATING", "ACKNOWLEDGED", "DISMISSED", "RESOLVED"]
    target = body.status.upper()
    if target not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid story status: {body.status}")

    story.status = target
    await db.commit()
    return {"story_id": story.id, "status": story.status}


@router.get("/{story_id}/timeline", response_model=List[StoryTimelineItem], summary="Get Chronological Story Event Timeline")
async def get_story_timeline(story_id: str, db: AsyncSession = Depends(get_db)) -> List[StoryTimelineItem]:
    res_s = await db.execute(select(Story).where(Story.id == story_id))
    story = res_s.scalars().first()
    if not story:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Story {story_id} not found.")

    art_res = await db.execute(
        select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
            story_articles.c.story_id == story_id
        ).order_by(Article.published_at.asc())
    )
    articles = art_res.scalars().all()

    timeline_items: List[StoryTimelineItem] = []
    for a in articles:
        # Check claims for this article
        res_cl = await db.execute(select(Claim).where(Claim.article_id == a.id))
        claim = res_cl.scalars().first()

        # Check media extractions if available
        res_med = await db.execute(select(Media).where(Media.id == a.id))
        med = res_med.scalars().first()
        media_meta = None
        if med:
            media_meta = {
                "media_id": med.id,
                "media_type": med.media_type,
                "filename": med.filename,
                "extraction_method": med.extractions[0].extraction_method if med.extractions else "DIRECT_EXTRACT",
                "extracted_content": med.extractions[0].extracted_content[:150] if med.extractions else "",
            }

        timeline_items.append(
            StoryTimelineItem(
                id=f"timeline-{a.id}",
                timestamp=a.published_at,
                event_type="PRIMARY_SIGNAL" if a.is_original_reporting else "CORROBORATING_REPORT",
                title=a.title,
                source_name=a.attribution_text,
                language=a.language or "en",
                claim_statement=claim.statement if claim else a.excerpt[:120],
                evidence_excerpt=a.excerpt,
                media_metadata=media_meta,
            )
        )

    timeline_items.sort(key=lambda t: t.timestamp)
    return timeline_items


@router.get("/{story_id}/contradictions", response_model=List[ContradictionDetailItem], summary="Get Story Contradictions")
async def get_story_contradictions(story_id: str, db: AsyncSession = Depends(get_db)) -> List[ContradictionDetailItem]:
    res = await db.execute(select(Contradiction).where(Contradiction.story_id == story_id))
    contradictions = res.scalars().all()

    claim_ids = [c.claim_a_id for c in contradictions] + [c.claim_b_id for c in contradictions]
    claims_map: Dict[str, Claim] = {}
    if claim_ids:
        cl_res = await db.execute(select(Claim).where(Claim.id.in_(claim_ids)))
        for cl in cl_res.scalars().all():
            claims_map[cl.id] = cl

    return [
        ContradictionDetailItem(
            id=c.id,
            story_id=c.story_id,
            claim_a_id=c.claim_a_id,
            claim_b_id=c.claim_b_id,
            claim_a_statement=claims_map.get(c.claim_a_id).statement if c.claim_a_id in claims_map else c.conflict_metadata.get("claim_a_statement", "Claim A"),
            claim_b_statement=claims_map.get(c.claim_b_id).statement if c.claim_b_id in claims_map else c.conflict_metadata.get("claim_b_statement", "Claim B"),
            claim_a_source=claims_map.get(c.claim_a_id).metadata_json.get("source", "Source A") if c.claim_a_id in claims_map else "Source A",
            claim_b_source=claims_map.get(c.claim_b_id).metadata_json.get("source", "Source B") if c.claim_b_id in claims_map else "Source B",
            is_load_bearing=c.is_load_bearing,
            status=c.status,
            severity=c.severity,
            description=c.description,
            halted_prediction=c.halted_prediction,
            detected_at=c.conflict_metadata.get("detected_at"),
        )
        for c in contradictions
    ]


@router.post("/{story_id}/contradictions/{contradiction_id}/resolve", summary="Resolve a Contradiction")
async def resolve_contradiction(
    story_id: str,
    contradiction_id: str,
    body: ResolveContradictionRequest,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Contradiction).where(Contradiction.id == contradiction_id, Contradiction.story_id == story_id)
    )
    contradiction = res.scalars().first()
    if not contradiction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contradiction not found.")

    contradiction.status = "RESOLVED"
    contradiction.halted_prediction = False
    contradiction.resolution_notes = body.resolution_notes
    await db.commit()

    # Re-evaluate Contradiction Gate on Story
    res_story = await db.execute(select(Story).where(Story.id == story_id))
    story = res_story.scalars().first()
    if story:
        art_res = await db.execute(
            select(Article).join(story_articles, story_articles.c.article_id == Article.id).where(
                story_articles.c.story_id == story_id
            )
        )
        articles_db = art_res.scalars().all()
        gate_res = await ContradictionService.evaluate_contradiction_gate(db, story_id, articles_db)

        story.contradiction_status = gate_res.contradiction_status
        story.prediction_eligible = gate_res.prediction_eligible
        await db.commit()

        # If alert exists, update alert contradiction status
        res_alt = await db.execute(select(Alert).where(Alert.story_id == story_id))
        alert_db = res_alt.scalars().first()
        if alert_db:
            alert_db.contradiction_status = gate_res.contradiction_status
            alert_db.prediction_status = "ELIGIBLE" if gate_res.prediction_eligible else "BLOCKED"
            alert_db.has_unresolved_contradictions = not gate_res.prediction_eligible
            if gate_res.prediction_eligible and alert_db.status == "BLOCKED":
                alert_db.status = "ACTIVE"
                alert_db.ranking_explanation = "Contradiction resolved by analyst. Early alert active."
            await db.commit()

    return {
        "status": "success",
        "contradiction_id": contradiction_id,
        "new_contradiction_status": story.contradiction_status if story else "RESOLVED",
        "prediction_eligible": story.prediction_eligible if story else True,
    }
