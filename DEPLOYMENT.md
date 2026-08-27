# Pre-Headline Intelligence — Deployment & Operations Guide

## 1. Prerequisites & Runtime Stack

- **Backend Runtime**: Python 3.11+ / 3.12 / 3.14
- **Frontend Runtime**: Node.js 18+ (Next.js 14 App Router)
- **Database**: PostgreSQL 15+ with `pgvector` extension enabled (or SQLite for isolated testing)
- **Cache & Queue**: Redis 7+ (optional in single-instance mode)

---

## 2. Environment Configuration

### Backend Environment Variables (`backend/.env`)

```ini
# Application Identity
APP_NAME="Pre-Headline Intelligence"
APP_VERSION="0.1.0"
APP_ENV="production"             # Options: development, testing, production
DEBUG=false
API_V1_STR="/api/v1"
SECRET_KEY="<generate-secure-random-256-bit-key>"

# Database Configuration
DATABASE_URL="postgresql+asyncpg://postgres:<password>@localhost:5432/pre_headline_intel"
DATABASE_SYNC_URL="postgresql://postgres:<password>@localhost:5432/pre_headline_intel"

# Redis & Background Tasks
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# External Ingestion Services
GDELT_API_URL="https://api.gdeltproject.org/api/v2/gkg/gkg"
GDELT_ENABLED=true
NEWS_API_KEY=""

# LLM Reasoning & Grounded Copilot
LLM_PROVIDER="openai"            # Options: openai, gemini, anthropic, mock
LLM_API_KEY="<your-llm-api-key>"
LLM_MODEL="gpt-4o-mini"
LLM_TEMPERATURE=0.1
LLM_CACHE_ENABLED=true

# Multilingual Embeddings
EMBEDDING_MODEL_NAME="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIMENSION=384

# Media Storage
MEDIA_STORAGE_BACKEND="local"    # Options: local, s3
MEDIA_STORAGE_PATH="./uploads"
MEDIA_MAX_FILE_SIZE_MB=50

# CORS Security
CORS_ORIGINS="http://localhost:3000,https://app.preheadline.intelligence"
```

### Frontend Environment Variables (`frontend/.env.local`)

```ini
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1"
```

---

## 3. Database Migration & Initialization

```bash
cd backend

# Initialize Alembic / run migrations
alembic upgrade head

# Seed initial evaluation fixtures and test scenarios
python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.replay_engine import ReplayEngine

async def init():
    async with AsyncSessionLocal() as session:
        await ReplayEngine.seed_scenarios_if_empty(session)

asyncio.run(init())
"
```

---

## 4. Starting Production Services

### Backend (FastAPI with Uvicorn)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
```

### Frontend (Next.js Standalone Build)

```bash
cd frontend
npm run build
npm run start -- -p 3000
```

---

## 5. Health Probes & Monitoring

| Endpoint | Method | Purpose | Response |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Overall service health summary | `200 OK` + Service metadata |
| `/health/live` | `GET` | Kubernetes Liveness Probe | `200 OK` `{"status": "live"}` |
| `/health/ready` | `GET` | Kubernetes Readiness Probe (DB Check) | `200 OK` `{"status": "ready", "database": "connected"}` |
