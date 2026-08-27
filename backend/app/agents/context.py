import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent
from app.schemas.agent import (
    ContextInput,
    ContextOutput,
    EnrichedArticle,
    ExtractedEntityItem,
    ExtractedEventItem,
    ExtractedClaim,
    DiscoveredCandidate,
)
from app.models.article import Article
from app.services.context_service import ContextService
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class ContextAgent(BaseAgent[ContextInput, ContextOutput]):
    """
    Agent 2 — Context (Phase 2 Real Implementation)
    Purpose: Evaluates explainable relevance, extracts structured entities & events,
    and integrates articles into the Media Event Graph.
    """
    agent_id = 2
    agent_name = "Context Agent"
    description = "Enriches articles with normalized entities, structured events, and explainable relevance filtering."

    async def process(self, input_data: ContextInput, db: Optional[AsyncSession] = None) -> ContextOutput:
        # Prepare list of articles to process
        articles_to_process: List[DiscoveredCandidate] = list(input_data.raw_articles)
        if not articles_to_process and (input_data.title or input_data.article_id):
            articles_to_process.append(
                DiscoveredCandidate(
                    title=input_data.title or "Signal",
                    url=input_data.article_id or "local://article",
                    source_name="Input Article",
                    language="en",
                    excerpt=input_data.excerpt or "",
                )
            )

        logger.info(f"[{self.agent_name}] Processing {len(articles_to_process)} candidate articles for context extraction.")

        enriched_articles: List[EnrichedArticle] = []
        relevant_count = 0
        filtered_count = 0

        # Extract watchlist keywords
        watchlist_keywords: List[str] = list(input_data.tracked_entities)
        if input_data.watchlist_definitions:
            for w in input_data.watchlist_definitions.values():
                if isinstance(w, list):
                    watchlist_keywords.extend(w)
                elif isinstance(w, str):
                    watchlist_keywords.append(w)

        primary_entities: List[ExtractedEntityItem] = []
        primary_events: List[ExtractedEventItem] = []
        primary_is_relevant = True
        primary_reason = "Context enriched."

        for candidate in articles_to_process:
            text = f"{candidate.title}\n{candidate.excerpt or ''}"
            
            # 1. Extract Entities
            extracted_entities_data = ContextService.extract_entities(text, language=candidate.language)
            
            # 2. Extract Events
            extracted_events_data = ContextService.extract_events(text, extracted_entities_data, language=candidate.language)

            # 3. Evaluate Explainable Relevance
            is_rel, rel_score, matched_ents, rel_reason = ContextService.evaluate_relevance(
                text=text,
                entities=extracted_entities_data,
                events=extracted_events_data,
                watchlist_keywords=watchlist_keywords if watchlist_keywords else None,
            )

            if is_rel:
                relevant_count += 1
            else:
                filtered_count += 1

            schema_entities = [
                ExtractedEntityItem(
                    name=e.canonical_name,
                    entity_type=e.entity_type,
                    confidence=e.confidence,
                    aliases=[e.raw_mention],
                )
                for e in extracted_entities_data
            ]

            schema_events = [
                ExtractedEventItem(
                    event_type=ev.event_type,
                    title=ev.title,
                    timestamp=datetime.now(timezone.utc),
                    location=ev.location,
                    confidence=ev.confidence,
                )
                for ev in extracted_events_data
            ]

            if not primary_entities and schema_entities:
                primary_entities = schema_entities
                primary_events = schema_events
                primary_is_relevant = is_rel
                primary_reason = rel_reason

            # 4. If DB session available, upsert graph nodes & edges
            if db is not None:
                art_res = await db.execute(select(Article).where(Article.url == candidate.url))
                article_db = art_res.scalars().first()
                if article_db:
                    await GraphService.build_article_graph_context(
                        db=db,
                        article=article_db,
                        extracted_entities=extracted_entities_data,
                        extracted_events=extracted_events_data,
                    )

            enriched = EnrichedArticle(
                article_id=candidate.url,
                title=candidate.title,
                url=candidate.url,
                language=candidate.language,
                is_relevant=is_rel,
                relevance_score=rel_score,
                extracted_entities=schema_entities,
                extracted_events=schema_events,
                extracted_claims=[],
                summary=f"Relevance: {rel_reason}",
            )
            enriched_articles.append(enriched)

        return ContextOutput(
            status="success",
            article_id=input_data.article_id or (articles_to_process[0].url if articles_to_process else None),
            is_confirmed_relevant=primary_is_relevant,
            relevance_reason=primary_reason,
            extracted_entities=primary_entities,
            extracted_events=primary_events,
            enriched_articles=enriched_articles,
            total_processed=len(enriched_articles),
            relevant_count=relevant_count,
            filtered_count=filtered_count,
        )
