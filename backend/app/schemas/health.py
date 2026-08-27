from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Operational status of the backend")
    app_name: str = Field(default="Pre-Headline Intelligence", description="Application name")
    version: str = Field(default="0.1.0", description="Application semantic version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of health probe")
    database: str = Field(default="ready", description="Database connection status")
    phase: str = Field(default="Phase 0: Foundation", description="Current development phase")
