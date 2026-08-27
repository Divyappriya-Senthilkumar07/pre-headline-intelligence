from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.media import MediaRead


class RssTriggerRequest(BaseModel):
    feed_url: Optional[str] = None
    feed_name: Optional[str] = None
    language: Optional[str] = None


class RssTriggerResponse(BaseModel):
    status: str = "success"
    feeds_processed: int
    new_articles_total: int
    duplicates_skipped_total: int
    details: List[Dict[str, Any]] = Field(default_factory=list)


class GdeltTriggerRequest(BaseModel):
    query_topic: Optional[str] = None


class GdeltTriggerResponse(BaseModel):
    status: str = "success"
    total_records: int
    new_articles: int
    new_entities: int
    duplicates_skipped: int


class IngestedArticleSummary(BaseModel):
    id: str
    title: str
    source_name: str
    language: str
    published_at: datetime
    excerpt: str
    url: str


class IngestionDashboardResponse(BaseModel):
    total_media_count: int
    recent_media: List[MediaRead] = Field(default_factory=list)
    total_articles_count: int
    total_sources_count: int
    rss_status: str = "ACTIVE"
    gdelt_status: str = "ACTIVE"
    last_successful_ingestion: Optional[datetime] = None
    recent_articles: List[IngestedArticleSummary] = Field(default_factory=list)
