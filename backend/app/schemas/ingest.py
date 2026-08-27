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
    domain: Optional[str] = None
    language: str
    published_at: datetime
    excerpt: str
    url: str
    social_image: Optional[str] = None


class IngestionDashboardResponse(BaseModel):
    source: str = "GDELT_DOC_2.0 & RSS_FEEDS"
    current_status: str = "ONLINE"
    rss_status: str = "ACTIVE"
    gdelt_status: str = "ACTIVE"
    last_successful_ingestion: Optional[datetime] = None
    total_articles_count: int = 0
    total_sources_count: int = 0
    articles_fetched: int = 0
    articles_accepted: int = 0
    duplicates_skipped: int = 0
    errors: int = 0
    is_live_signal: bool = False
    total_media_count: int = 0
    recent_media: List[MediaRead] = Field(default_factory=list)
    recent_articles: List[IngestedArticleSummary] = Field(default_factory=list)
