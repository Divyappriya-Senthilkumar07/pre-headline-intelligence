import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models import Base


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """Verify that database connection executes queries cleanly."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_database_metadata_tables():
    """Verify that all core tables are declared in Base metadata."""
    expected_tables = {
        "users",
        "watchlists",
        "sources",
        "source_profiles",
        "articles",
        "entities",
        "events",
        "graph_edges",
        "claims",
        "stories",
        "story_articles",
        "story_entities",
        "evidence_chains",
        "contradictions",
        "predictions",
        "alerts",
        "feedbacks",
        "media",
        "media_processing_jobs",
        "media_extractions",
    }
    registered_tables = set(Base.metadata.tables.keys())
    for table in expected_tables:
        assert table in registered_tables, f"Table {table} missing from Base metadata"
