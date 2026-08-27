from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.watchlists import router as watchlists_router
from app.api.ingest import router as ingest_router
from app.api.stories import router as stories_router
from app.api.articles import router as articles_router
from app.api.entities import router as entities_router
from app.api.events import router as events_router
from app.api.pipeline import router as pipeline_router
from app.api.copilot import router as copilot_router
from app.api.alerts import router as alerts_router
from app.api.replay import router as replay_router
from app.api.evaluation import router as evaluation_router
from app.api.media import router as media_router

api_router = APIRouter()

# Health check route
api_router.include_router(health_router)

# Domain module routes
api_router.include_router(watchlists_router)
api_router.include_router(ingest_router)
api_router.include_router(stories_router)
api_router.include_router(articles_router)
api_router.include_router(entities_router)
api_router.include_router(events_router)
api_router.include_router(pipeline_router)
api_router.include_router(copilot_router)
api_router.include_router(alerts_router)
api_router.include_router(replay_router)
api_router.include_router(evaluation_router)
api_router.include_router(media_router)
