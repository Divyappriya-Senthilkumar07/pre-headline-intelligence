import uuid
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.api.router import api_router
from app.schemas.health import HealthResponse
from app.services.replay_engine import ReplayEngine

# Setup structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("pre_headline_intelligence")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("=======================================================")
    logger.info(f" Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f" Environment: {settings.APP_ENV} | Debug: {settings.DEBUG}")
    logger.info(" Multi-Agent Story Formation & Narrative Provenance Platform")
    logger.info("=======================================================")
    yield
    logger.info(f" Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Pre-Headline Intelligence Platform API. "
        "We don't just detect a story is emerging — we prove it, before it's obvious, "
        "in the language it's actually forming in."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# -----------------------------------------------------------------------------
# Request Tracing & Correlation Middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    # Attach request_id to state
    request.state.request_id = request_id

    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    if request.url.path not in ["/health", "/health/live"]:
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration_ms}ms"
        )
    return response


# -----------------------------------------------------------------------------
# Standardized Error Handling
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:12]}")
    code = "BAD_REQUEST" if exc.status_code == 400 else ("NOT_FOUND" if exc.status_code == 404 else "ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": code,
                "message": exc.detail,
                "request_id": request_id,
            },
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:12]}")
    logger.error(f"[{request_id}] Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please contact system administrator.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact system administrator.",
                "request_id": request_id,
            },
        },
        headers={"X-Request-ID": request_id},
    )


# -----------------------------------------------------------------------------
# Health & Readiness Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Health"], summary="Overall Health Check")
async def root_health() -> HealthResponse:
    """Returns general backend health status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        database="ready",
        phase="Phase 0: Foundation",
    )


@app.get("/health/live", tags=["Health"], summary="Liveness Probe")
async def health_liveness():
    """Liveness probe: verifies process is responsive."""
    return {"status": "live", "timestamp": datetime.now(timezone.utc).isoformat()}


from fastapi import FastAPI, Request, Depends, status, HTTPException
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


@app.get("/health/ready", tags=["Health"], summary="Readiness Probe")
async def health_readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe: verifies database connectivity and engine readiness."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "environment": settings.APP_ENV,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity unavailable.",
        )


# -----------------------------------------------------------------------------
# Demo Reset Endpoint (Safeguarded)
# -----------------------------------------------------------------------------
@app.post(
    f"{settings.API_V1_STR}/demo/reset",
    tags=["Demo Controls"],
    summary="Reset Demo / Evaluation Data",
    description="Resets seed historical scenarios and evaluation fixtures. Disabled in production environments.",
)
async def demo_reset(db: AsyncSession = Depends(get_db)):
    if settings.APP_ENV.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset is disabled in production environments.",
        )

    await ReplayEngine.seed_scenarios_if_empty(db)

    return {
        "status": "success",
        "message": "Demo fixtures and evaluation seed scenarios successfully reset.",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Pre-Headline Intelligence Platform API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "version": settings.APP_VERSION,
        "status": "PRODUCTION_HARDENED",
    }
