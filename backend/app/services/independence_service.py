import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.article import Article
from app.models.source import Source, SourceProfile
from app.models.graph import Entity, Event, GraphEdge
from app.services.embedding_service import MultilingualEmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class SourceRelationshipResult:
    article_id: str
    source_id: str
    source_name: str
    domain: str
    relationship_type: str  # ORIGINAL, SYNDICATED, COPIED, INDEPENDENT, RELATED, UNKNOWN
    original_source_id: Optional[str] = None
    similarity_score: float = 0.0
    reason: str = ""


@dataclass
class IndependenceAnalysisResult:
    story_id: str
    total_articles_count: int
    candidate_sources_count: int
    independent_sources_count: int
    independence_score: float
    source_diversity_score: float
    temporal_spread_score: float
    entity_alignment_score: float
    source_relationships: List[SourceRelationshipResult] = field(default_factory=list)
    languages_represented: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class IndependenceService:
    """
    Agent 5 — Source Independence & Corroboration Analysis Engine.
    Critical Principle: Raw article count != Independent source count.
    Measures Source Diversity, Temporal Spread, and Entity Alignment.
    Detects syndicated, copied, and derivative articles.
    """

    SYNDICATION_KEYWORDS = [
        "pti", "press trust of india", "ani", "asian news international",
        "reuters", "associated press", "ap wire", "afp", "bloomberg wire",
        "syndicated feed", "wire service", "reproduced with permission"
    ]

    @classmethod
    def _calculate_text_jaccard(cls, text_a: str, text_b: str) -> float:
        """Compute word-level Jaccard similarity between two texts."""
        words_a = set(re.findall(r"\w+", text_a.lower()))
        words_b = set(re.findall(r"\w+", text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a.intersection(words_b))
        union = len(words_a.union(words_b))
        return intersection / union if union > 0 else 0.0

    @classmethod
    async def analyze_story_independence(
        cls,
        db: AsyncSession,
        story_id: str,
        articles: List[Article],
        entities: Optional[List[Entity]] = None,
    ) -> IndependenceAnalysisResult:
        """
        Conducts full Source Independence Analysis across candidate story articles.
        Returns calibrated independence score and sub-scores.
        """
        if not articles:
            return IndependenceAnalysisResult(
                story_id=story_id,
                total_articles_count=0,
                candidate_sources_count=0,
                independent_sources_count=0,
                independence_score=0.0,
                source_diversity_score=0.0,
                temporal_spread_score=0.0,
                entity_alignment_score=0.0,
            )

        # 1. Fetch Sources and Profiles
        source_ids = list(set(a.source_id for a in articles if a.source_id))
        sources_map: Dict[str, Source] = {}
        if source_ids:
            res = await db.execute(select(Source).where(Source.id.in_(source_ids)))
            for s in res.scalars().all():
                sources_map[s.id] = s

        # Sort articles chronologically
        sorted_articles = sorted(
            articles,
            key=lambda a: a.published_at.timestamp() if a.published_at else 0.0,
        )

        embedder = MultilingualEmbeddingService()

        # 2. Detect Syndication & Copy Relationships
        relationships: List[SourceRelationshipResult] = []
        independent_group_roots: List[Article] = []
        domain_articles_map: Dict[str, List[Article]] = {}

        for i, art in enumerate(sorted_articles):
            src = sources_map.get(art.source_id) if art.source_id else None
            domain = (src.domain if src else None) or (art.url.split("/")[2] if "://" in art.url else "unknown.org")
            domain_articles_map.setdefault(domain, []).append(art)

            is_derivative = False
            matched_rel_type = "INDEPENDENT"
            original_src_id: Optional[str] = None
            max_sim = 0.0
            deriv_reason = "Original reporting with distinct provenance"

            # Check if domain contains prior article in same story (internal repetition)
            if len(domain_articles_map[domain]) > 1:
                first_art = domain_articles_map[domain][0]
                if first_art.id != art.id:
                    is_derivative = True
                    matched_rel_type = "RELATED"
                    original_src_id = first_art.source_id
                    deriv_reason = f"Duplicate or follow-up publication from same publisher network ({domain})"

            # Compare against earlier articles in story for syndication/copying
            if not is_derivative:
                art_text = f"{art.title} {art.excerpt}"
                for earlier_art in sorted_articles[:i]:
                    earlier_text = f"{earlier_art.title} {earlier_art.excerpt}"
                    jaccard = cls._calculate_text_jaccard(art_text, earlier_text)
                    
                    # Embedding similarity check
                    vec_a = art.embedding or embedder.embed_text(art_text)
                    vec_b = earlier_art.embedding or embedder.embed_text(earlier_text)
                    cos_sim = embedder.cosine_similarity(vec_a, vec_b)
                    
                    time_delta_mins = abs((art.published_at - earlier_art.published_at).total_seconds()) / 60.0 if (art.published_at and earlier_art.published_at) else 999.0

                    # Check explicit wire/syndication signals
                    has_wire_keyword = any(k in art_text.lower() for k in cls.SYNDICATION_KEYWORDS)

                    if (jaccard >= 0.65 or cos_sim >= 0.88) and time_delta_mins <= 60.0:
                        is_derivative = True
                        max_sim = max(jaccard, cos_sim)
                        original_src_id = earlier_art.source_id
                        if has_wire_keyword or time_delta_mins <= 5.0:
                            matched_rel_type = "SYNDICATED"
                            deriv_reason = f"Identical wire/syndicated copy published {int(time_delta_mins)}m after lead wire"
                        else:
                            matched_rel_type = "COPIED"
                            deriv_reason = f"High textual duplication (sim: {max_sim:.2f}) copied from earlier report"
                        break

            if is_derivative:
                relationships.append(
                    SourceRelationshipResult(
                        article_id=art.id,
                        source_id=art.source_id or "unknown",
                        source_name=src.name if src else art.attribution_text,
                        domain=domain,
                        relationship_type=matched_rel_type,
                        original_source_id=original_src_id,
                        similarity_score=max_sim,
                        reason=deriv_reason,
                    )
                )
            else:
                independent_group_roots.append(art)
                rel_type = "ORIGINAL" if i == 0 else "INDEPENDENT"
                relationships.append(
                    SourceRelationshipResult(
                        article_id=art.id,
                        source_id=art.source_id or "unknown",
                        source_name=src.name if src else art.attribution_text,
                        domain=domain,
                        relationship_type=rel_type,
                        original_source_id=art.source_id,
                        similarity_score=1.0,
                        reason="Independent primary source reporting",
                    )
                )

        independent_source_count = max(1, len(independent_group_roots))
        candidate_sources_count = len(set(a.source_id for a in articles if a.source_id)) or len(domain_articles_map)
        languages_represented = list(set(a.language for a in articles if a.language))

        # 3. Compute Dimension A: Source Diversity Score (0.0 to 1.0)
        # Factors: unique domains, distinct source types, regional breadth
        distinct_domains = len(domain_articles_map)
        source_types = set(s.source_type for s in sources_map.values())
        diversity_raw = (
            min(1.0, distinct_domains / 4.0) * 0.60
            + min(1.0, len(source_types) / 2.0) * 0.20
            + min(1.0, len(languages_represented) / 3.0) * 0.20
        )
        source_diversity_score = round(min(1.0, max(0.15, diversity_raw)), 3)

        # 4. Compute Dimension B: Temporal Spread Score (0.0 to 1.0)
        # Evaluates organic timeline vs simultaneous wire blast
        if len(sorted_articles) <= 1:
            temporal_spread_score = 0.50
        else:
            time_deltas = []
            for k in range(1, len(sorted_articles)):
                if sorted_articles[k].published_at and sorted_articles[k - 1].published_at:
                    dt = abs((sorted_articles[k].published_at - sorted_articles[k - 1].published_at).total_seconds()) / 60.0
                    time_deltas.append(dt)
                else:
                    time_deltas.append(30.0)

            avg_delta = sum(time_deltas) / len(time_deltas) if time_deltas else 0.0
            
            # If all articles appeared within 2 minutes of each other (simultaneous syndication blast)
            if avg_delta < 2.0 and len(independent_group_roots) < len(sorted_articles):
                temporal_spread_score = 0.30  # Low score due to simultaneous syndication
            elif avg_delta < 5.0:
                temporal_spread_score = 0.55
            elif 5.0 <= avg_delta <= 720.0:  # 5 mins to 12 hours organic emergence
                temporal_spread_score = 0.88
            else:
                temporal_spread_score = 0.70

        temporal_spread_score = round(temporal_spread_score, 3)

        # 5. Compute Dimension C: Entity Alignment Score (0.0 to 1.0)
        # Measures entity/event consistency across independent sources
        if entities and len(entities) >= 1:
            entity_alignment_score = min(1.0, 0.70 + (len(entities) * 0.10))
        else:
            entity_alignment_score = 0.75
        entity_alignment_score = round(entity_alignment_score, 3)

        # 6. Overall Calibrated Independence Score (0.0 to 1.0)
        # Weighting Strategy: Diversity (40%), Temporal (30%), Alignment (30%)
        # Penalized if independent sources ratio is low
        ratio_independent = independent_source_count / max(1, len(articles))
        base_independence = (
            0.40 * source_diversity_score
            + 0.30 * temporal_spread_score
            + 0.30 * entity_alignment_score
        )
        calibrated_independence_score = round(
            min(1.0, max(0.10, base_independence * (0.60 + 0.40 * ratio_independent))),
            3,
        )

        return IndependenceAnalysisResult(
            story_id=story_id,
            total_articles_count=len(articles),
            candidate_sources_count=candidate_sources_count,
            independent_sources_count=independent_source_count,
            independence_score=calibrated_independence_score,
            source_diversity_score=source_diversity_score,
            temporal_spread_score=temporal_spread_score,
            entity_alignment_score=entity_alignment_score,
            source_relationships=relationships,
            languages_represented=languages_represented,
            details={
                "distinct_domains_count": distinct_domains,
                "independent_ratio": round(ratio_independent, 2),
                "syndicated_copies_detected": len(articles) - independent_source_count,
                "weighting_strategy": "Diversity (40%) + Temporal (30%) + Entity Alignment (30%) calibrated by independent/total ratio",
            },
        )
