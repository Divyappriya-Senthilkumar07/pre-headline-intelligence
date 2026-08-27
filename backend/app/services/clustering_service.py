import uuid
import numpy as np
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.story import Story, story_articles, story_entities
from app.models.article import Article
from app.models.graph import Entity, GraphEdge
from app.services.embedding_service import MultilingualEmbeddingService

logger = logging.getLogger(__name__)


class ClusterOutputData:
    def __init__(
        self,
        cluster_id: int,
        article_ids: List[str],
        articles: List[Article],
        entities: List[Entity],
        working_title: str,
        languages: List[str],
        cluster_density: float = 0.85,
    ):
        self.cluster_id = cluster_id
        self.article_ids = article_ids
        self.articles = articles
        self.entities = entities
        self.working_title = working_title
        self.languages = languages
        self.cluster_density = cluster_density


class StoryClusteringService:
    """
    Agent 4 — Semantic Story Clustering Engine.
    Groups multilingual articles into candidate Story clusters using HDBSCAN and semantic vector similarity.
    """

    MIN_CLUSTER_SIZE: int = 2
    MIN_SAMPLES: int = 1

    @classmethod
    def run_hdbscan(
        cls,
        embeddings: List[List[float]],
        min_cluster_size: Optional[int] = None,
        min_samples: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executes HDBSCAN on dense embeddings.
        Returns (labels, probabilities). Noise points receive label -1.
        """
        req_size = min_cluster_size if min_cluster_size is not None else cls.MIN_CLUSTER_SIZE
        if len(embeddings) < req_size:
            return np.array([-1] * len(embeddings)), np.array([0.0] * len(embeddings))

        X = np.array(embeddings, dtype=np.float32)

        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=req_size,
                min_samples=min_samples or cls.MIN_SAMPLES,
                metric="euclidean",
                allow_single_cluster=True,
                cluster_selection_epsilon=0.8,
            )
            clusterer.fit(X)
            
            # If HDBSCAN marked all points as noise, fallback to cosine distance clustering
            if all(l == -1 for l in clusterer.labels_):
                return cls._fallback_cosine_clustering(X, req_size)
            
            return clusterer.labels_, clusterer.probabilities_
        except Exception as e:
            logger.warning(f"[ClusteringService] HDBSCAN package fallback to cosine distance: {e}")
            return cls._fallback_cosine_clustering(X, req_size)

    @classmethod
    def _fallback_cosine_clustering(cls, X: np.ndarray, min_cluster_size: int) -> Tuple[np.ndarray, np.ndarray]:
        """High-precision deterministic distance clusterer fallback."""
        n = len(X)
        labels = np.array([-1] * n)
        probs = np.array([0.0] * n)

        # Pairwise dot product (cosine similarity for normalized unit vectors)
        sim_matrix = np.dot(X, X.T)
        cluster_id = 0
        assigned = set()

        for i in range(n):
            if i in assigned:
                continue
            neighbors = [j for j in range(n) if sim_matrix[i, j] >= 0.50]
            if len(neighbors) >= min_cluster_size:
                for idx in neighbors:
                    labels[idx] = cluster_id
                    probs[idx] = float(sim_matrix[i, idx])
                    assigned.add(idx)
                cluster_id += 1

        return labels, probs

    @classmethod
    async def cluster_articles(
        cls,
        db: AsyncSession,
        articles: List[Article],
        min_cluster_size: Optional[int] = None,
        include_singletons: bool = False,
    ) -> List[Story]:
        if not articles:
            logger.info("[ClusteringService] No articles available for clustering.")
            return []

        # 1. Ensure all articles have embeddings
        embed_service = MultilingualEmbeddingService()
        embeddings: List[List[float]] = []
        for art in articles:
            if art.embedding is not None and len(art.embedding) == embed_service.DIMENSION:
                embeddings.append(list(art.embedding))
            else:
                vec = embed_service.embed_text(f"{art.title} {art.excerpt}")
                art.embedding = vec
                embeddings.append(vec)

        await db.commit()

        # 2. Run HDBSCAN
        labels, probs = cls.run_hdbscan(embeddings, min_cluster_size=min_cluster_size)

        # 3. Group by valid cluster labels
        clusters_map: Dict[int, List[Article]] = {}
        noise_articles: List[Article] = []

        for idx, label in enumerate(labels):
            if label == -1:
                noise_articles.append(articles[idx])
            else:
                clusters_map.setdefault(int(label), []).append(articles[idx])

        # If singletons are allowed, assign individual clusters to distinct noise articles
        if include_singletons and noise_articles:
            next_cluster_id = max(clusters_map.keys(), default=-1) + 1
            for na in noise_articles:
                clusters_map[next_cluster_id] = [na]
                next_cluster_id += 1

        logger.info(f"[ClusteringService] Formed {len(clusters_map)} candidate story clusters.")

        created_stories: List[Story] = []

        # 4. Create Story records for clusters
        for cluster_id, cluster_articles_list in clusters_map.items():
            article_ids = [a.id for a in cluster_articles_list]
            languages = list(set(a.language for a in cluster_articles_list if a.language))

            # Retrieve connected entities across cluster articles
            res = await db.execute(
                select(GraphEdge.target_node_id).where(
                    GraphEdge.source_node_id.in_(article_ids),
                    GraphEdge.edge_type == "mentions",
                )
            )
            entity_ids = list(set(res.scalars().all()))
            
            entities = []
            if entity_ids:
                ent_res = await db.execute(select(Entity).where(Entity.id.in_(entity_ids)))
                entities = ent_res.scalars().all()

            # Generate descriptive working title
            lead_article = cluster_articles_list[0]
            lead_title = lead_article.title.strip()
            primary_entity = entities[0].canonical_name if entities else (lead_article.attribution_text or "Intelligence Signal")
            
            if len(cluster_articles_list) > 1:
                working_title = f"{primary_entity}: {lead_title[:75]}"
            else:
                working_title = f"{lead_title[:90]}"

            story_id = str(uuid.uuid4())
            story = Story(
                id=story_id,
                title=working_title,
                why_it_matters=f"Candidate intelligence signal with {len(cluster_articles_list)} reporting sources across {len(languages)} language(s).",
                status="EMERGING",
                total_articles_count=len(cluster_articles_list),
                languages=languages,
                metadata_json={
                    "cluster_id": cluster_id,
                    "cluster_size": len(cluster_articles_list),
                    "languages": languages,
                    "article_ids": article_ids,
                    "entity_names": [e.canonical_name for e in entities],
                    "clustered_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            db.add(story)
            await db.flush()

            # Populate story_articles join table
            for art in cluster_articles_list:
                await db.execute(
                    story_articles.insert().values(
                        story_id=story.id,
                        article_id=art.id,
                    )
                )

            # Populate story_entities join table
            for ent in entities:
                await db.execute(
                    story_entities.insert().values(
                        story_id=story.id,
                        entity_id=ent.id,
                    )
                )

            created_stories.append(story)

        await db.commit()
        return created_stories
