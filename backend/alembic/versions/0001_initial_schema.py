"""Initial Schema for Pre-Headline Intelligence Platform

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-26 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. Watchlists
    op.create_table(
        "watchlists",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. Sources
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("domain", sa.String(length=255), nullable=True, unique=True, index=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, default="REGIONAL_MEDIA"),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("primary_language", sa.String(length=10), nullable=False, default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 4. Source Profiles
    op.create_table(
        "source_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("sources.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("independence_score", sa.Float(), nullable=False, default=0.5),
        sa.Column("syndication_links", sa.JSON(), nullable=False),
        sa.Column("corporate_owner", sa.String(length=255), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=False, default=0.7),
        sa.Column("historical_original_rate", sa.Float(), nullable=False, default=0.5),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Articles (with vector column)
    op.create_table(
        "articles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False, unique=True, index=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("language", sa.String(length=10), nullable=False, default="en", index=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("attribution_text", sa.String(length=500), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("is_original_reporting", sa.Boolean(), default=True),
        sa.Column("syndication_origin_id", sa.String(length=36), sa.ForeignKey("articles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 6. Entities
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("gdelt_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Events
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), default=0.8),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Graph Edges (PostgreSQL adjacency list)
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_node_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("target_node_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("edge_type", sa.String(length=100), nullable=False, index=True),
        sa.Column("weight", sa.Float(), default=1.0),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_graph_edge_source_target", "graph_edges", ["source_node_id", "target_node_id", "edge_type"])

    # 9. Claims (with vector column)
    op.create_table(
        "claims",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("article_id", sa.String(length=36), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=50), nullable=False, default="FACT"),
        sa.Column("is_load_bearing", sa.Boolean(), default=False, index=True),
        sa.Column("confidence", sa.Float(), default=0.8),
        sa.Column("language", sa.String(length=10), default="en"),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 10. Stories
    op.create_table(
        "stories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), default="EMERGING", index=True),
        sa.Column("formation_score", sa.Float(), default=0.0, index=True),
        sa.Column("independent_sources_count", sa.Integer(), default=1),
        sa.Column("total_articles_count", sa.Integer(), default=1),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("earliest_signal_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_signal_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estimated_mainstream_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lead_time_hours", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Join table: story_articles
    op.create_table(
        "story_articles",
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("article_id", sa.String(length=36), sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 12. Join table: story_entities
    op.create_table(
        "story_entities",
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("entity_id", sa.String(length=36), sa.ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relevance_weight", sa.Float(), default=1.0),
    )

    # 13. Evidence Chains
    op.create_table(
        "evidence_chains",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claim_id", sa.String(length=36), sa.ForeignKey("claims.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("step_order", sa.Integer(), default=1, index=True),
        sa.Column("evidence_type", sa.String(length=50), default="ARTICLE_EXCERPT"),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("supporting_quote", sa.Text(), nullable=True),
        sa.Column("corroborating_sources_count", sa.Integer(), default=1),
        sa.Column("confidence_score", sa.Float(), default=0.8),
        sa.Column("provenance_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 14. Contradictions
    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claim_a_id", sa.String(length=36), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_b_id", sa.String(length=36), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_load_bearing", sa.Boolean(), default=True, index=True),
        sa.Column("status", sa.String(length=50), default="UNRESOLVED", index=True),
        sa.Column("severity", sa.String(length=50), default="CRITICAL"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("halted_prediction", sa.Boolean(), default=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("conflict_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Predictions
    op.create_table(
        "predictions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("formation_score", sa.Float(), default=0.0),
        sa.Column("dimension_breakdown", sa.JSON(), nullable=False),
        sa.Column("probability", sa.Float(), default=0.5),
        sa.Column("impact", sa.Float(), default=0.5),
        sa.Column("trajectory_stage", sa.String(length=50), default="EARLY"),
        sa.Column("estimated_mainstream_hours", sa.Float(), nullable=True),
        sa.Column("is_halted", sa.Boolean(), default=False),
        sa.Column("halt_reason", sa.String(length=500), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("theoretical_framework", sa.String(length=100), default="Ansoff-Hiltunen Weak Signal Model"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 16. Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("story_id", sa.String(length=36), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("urgency", sa.Float(), default=0.5),
        sa.Column("probability", sa.Float(), default=0.5),
        sa.Column("impact", sa.Float(), default=0.5),
        sa.Column("rank_score", sa.Float(), default=0.125, index=True),
        sa.Column("formation_confidence", sa.String(length=50), default="MEDIUM"),
        sa.Column("independent_sources_count", sa.Integer(), default=1),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("has_unresolved_contradictions", sa.Boolean(), default=False),
        sa.Column("estimated_lead_time_hours", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), default="ACTIVE", index=True),
        sa.Column("alert_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 17. Feedbacks
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("alert_id", sa.String(length=36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("is_positive", sa.Boolean(), default=True),
        sa.Column("score", sa.Integer(), default=1),
        sa.Column("feedback_type", sa.String(length=50), default="ACCURATE_FORMATION"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 18. Media
    op.create_table(
        "media",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("media_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("upload_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_status", sa.String(length=50), nullable=False, default="UPLOADED", index=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("storage_reference", sa.String(length=1000), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 19. Media Processing Jobs
    op.create_table(
        "media_processing_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("media_id", sa.String(length=36), sa.ForeignKey("media.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, default="QUEUED", index=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("job_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 20. Media Extractions
    op.create_table(
        "media_extractions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("media_id", sa.String(length=36), sa.ForeignKey("media.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("extraction_type", sa.String(length=100), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extracted_entities", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), default=1.0),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("media_extractions")
    op.drop_table("media_processing_jobs")
    op.drop_table("media")
    op.drop_table("feedbacks")
    op.drop_table("alerts")
    op.drop_table("predictions")
    op.drop_table("contradictions")
    op.drop_table("evidence_chains")
    op.drop_table("story_entities")
    op.drop_table("story_articles")
    op.drop_table("stories")
    op.drop_table("claims")
    op.drop_table("graph_edges")
    op.drop_table("events")
    op.drop_table("entities")
    op.drop_table("articles")
    op.drop_table("source_profiles")
    op.drop_table("sources")
    op.drop_table("watchlists")
    op.drop_table("users")
