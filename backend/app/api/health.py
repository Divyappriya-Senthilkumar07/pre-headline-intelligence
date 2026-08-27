from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns backend service operational status and environment information.",
)
async def health_check() -> HealthResponse:
    """
    GET /health endpoint.
    Confirms that the FastAPI backend is initialized and responding.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        database="ready",
        phase="Phase 7: Production Ready",
    )
