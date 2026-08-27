# Pre-Headline Intelligence

> **Story Formation Intelligence & Narrative Provenance Platform**  
> *"We don't just detect a story is emerging — we prove it, before it's obvious, in the language it's actually forming in."*  
> Demo closing thesis: *"We didn't wait for the headline. We proved the story was forming."*

---

## 1. Executive Summary & Problem Solved

Traditional media monitoring systems (Meltwater, Cision, Google Alerts) tell you what has **already happened** after a story is published and indexed. Social monitoring platforms (NewsWhip) track post-publication engagement velocity. Weak-signal alerting tools (Dataminr) fire unverified leads at high volume, forcing analysts to manually verify every alert.

**Pre-Headline Intelligence** operates in the **fragment → emerging story → corroborated story** lifecycle stage before a story reaches mainstream national headlines.

Crucially, it is **NOT** an AI news aggregator, generic news monitor, or summarizer. It is a **reasoning and provenance engine** built around three strict pillars:

### The Three Core Pillars

1. **Independent-Source Corroboration**: Measures genuine source independence rather than raw mention count. 100 articles consisting of 5 independent reports and 95 syndicated wire copies are reported as **5 independent sources**, preventing syndication echo chambers from falsely inflating confidence.
2. **Mandatory Evidence Chain**: No alert or trajectory prediction may ever be emitted without a complete, traceable provenance chain:
   $$\text{Source} \longrightarrow \text{Extracted Claim} \longrightarrow \text{Supporting Evidence} \longrightarrow \text{Corroboration} \longrightarrow \text{Confidence}$$
3. **Contradiction Gate (Hard Stop in Code)**: If credible sources directly conflict on a *load-bearing claim* (a claim central to the conclusion), the system **halts** prediction and surfaces the conflict for investigation rather than averaging it away or hallucinating confidence.

---

## 2. Architecture & Pipeline

```
INGESTION (RSS / Licensed API / GDELT GKG)
   ↓
DEDUPLICATION (Near-duplicate & syndication graph detection)
   ↓
SEMANTIC DISCOVERY & CONTEXT FILTER (Agent 1 & Agent 2)
   ↓
ENTITY / EVENT / RELATION EXTRACTION → MEDIA EVENT GRAPH (Agent 3)
   ↓
STORY CLUSTERING (sentence-transformers + HDBSCAN) (Agent 4)
   ↓
INDEPENDENCE & CORROBORATION SCORING  ⟶  CONTRADICTION GATE (Agent 5)
   ↓
NARRATIVE TRACKING → STORY FORMATION SCORE (Ansoff/Hiltunen models) (Agent 6)
   ↓
TRAJECTORY & IMPACT PREDICTION (Probability × Impact Matrix) (Agent 7)
   ↓
EVIDENCE CHAIN ASSEMBLY & GROUNDED INVESTIGATION COPILOT (Agent 8)
   ↓
EARLY INTELLIGENCE ALERT EMISSION (Urgency × Probability × Impact) (Agent 9)
   ↓
ANALYST FEEDBACK → RE-RANKING MODEL
```

### The 9 Intelligence Agents

| Agent | Name | Phase 0 Interface Contract | Primary Responsibility |
|---|---|---|---|
| **Agent 1** | **Discovery** | `DiscoveryInput` $\rightarrow$ `DiscoveryOutput` | Ingests candidate signals matching tracked entities from RSS, GDELT, and licensed APIs. |
| **Agent 2** | **Context** | `ContextInput` $\rightarrow$ `ContextOutput` | Disambiguates keyword collisions and confirms genuine relevance. |
| **Agent 3** | **Expansion** | `ExpansionInput` $\rightarrow$ `ExpansionOutput` | Walks the knowledge graph outward to discover related regulators, documents, and entities. |
| **Agent 4** | **Story Clustering** | `StoryClusteringInput` $\rightarrow$ `StoryClusteringOutput` | Groups related articles into evolving story clusters using semantic embeddings. |
| **Agent 5** | **Independence & Corroboration** | `IndependenceInput` $\rightarrow$ `IndependenceOutput` | Computes source independence sub-scores and flags claim contradictions. |
| **Agent 6** | **Narrative & Formation** | `NarrativeFormationInput` $\rightarrow$ `NarrativeFormationOutput` | Produces the explainable 6-dimension Story Formation Score. |
| **Agent 7** | **Prediction** | `PredictionInput` $\rightarrow$ `PredictionOutput` | Projects trajectory stages and the Probability × Impact matrix. |
| **Agent 8** | **Evidence & Investigation** | `EvidenceInvestigationInput` $\rightarrow$ `EvidenceInvestigationOutput` | Assembles click-through evidence chains and powers the grounded copilot. |
| **Agent 9** | **Alert Orchestrator** | `AlertOrchestratorInput` $\rightarrow$ `AlertOrchestratorOutput` | Ranks alerts and enforces the Contradiction Gate guard clause. |

---

## 3. Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2
- **Database**: PostgreSQL with `pgvector` extension for multilingual embeddings
- **Graph Reasoning**: PostgreSQL adjacency-list tables (`graph_edges`) for lightweight, high-performance graph traversal without Neo4j overhead
- **Background Processing & Queues**: Redis & Celery (foundation configured)
- **Containerization**: Docker Compose

---

## 4. Phase Implementation Status

### ✅ Phase 0: Project Initialization & Foundation (Completed)
- [x] Clean modular project structure (`frontend/`, `backend/`, `database/`, `docs/`)
- [x] Next.js frontend with dark intelligence design system and placeholder routes:
  - `/` (Intelligence Feed)
  - `/stories/[id]` (Story Detail)
  - `/evidence/[id]` (Evidence Chain)
  - `/contradictions/[id]` (Contradiction Monitor)
  - `/replay/[scenario]` (Historical Replay)
- [x] FastAPI backend foundation with `GET /health` and modular API router mounts
- [x] PostgreSQL schema foundation with pgvector, 14 core entities, and adjacency-list graph edges
- [x] Media ingestion database and backend foundation (`Media`, `MediaProcessingJob`, `MediaExtraction` supporting states: `UPLOADED`, `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`)
- [x] All 9 intelligence agent interfaces typed and unit-testable
- [x] Alembic migration versions and Docker Compose setup
- [x] Automated test suite verifying models, agents, health checks, and database connections

### ⏳ Future Phases (Planned Roadmap — Do Not Implement Yet)
- **Phase 1**: Ingestion & Graph Foundation (GDELT GKG, RSS feeds, entity graph)
- **Phase 2**: Understanding (Multilingual embeddings + HDBSCAN clustering)
- **Phase 3**: Core Differentiators (Independence scoring, 6D Story Formation Score, Contradiction Gate)
- **Phase 4**: Prediction, Evidence, and Alerting Pipeline
- **Phase 5**: Full API & Dynamic UI Integration
- **Phase 6**: Historical Replay Engine & Measured Lead-Time Benchmarking
- **Phase 7**: Hardening & Cached Grounded Copilot

---

## 5. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose (optional for containerized run)

### Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```

### Option A: Running with Docker Compose
To start PostgreSQL (with pgvector), Redis, and the FastAPI backend:
```bash
docker-compose up --build
```
The backend will be accessible at `http://localhost:8000`.

---

### Option B: Running Locally for Development

#### 1. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations (when connected to PostgreSQL)
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Backend API documentation will be available at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Frontend application will be accessible at `http://localhost:3000`.

---

## 6. Running Tests

To run the backend test suite:
```bash
cd backend
python -m pytest tests/ -v
```

Verified tests cover:
1. Backend startup and `GET /health` probe
2. Database connection and Base metadata registration
3. Core database entities instantiation and persistence
4. All 9 intelligence agent execution contracts and Contradiction Gate guard clause
5. Media model lifecycle transitions (`UPLOADED` $\rightarrow$ `QUEUED` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` / `FAILED`)

---

## 7. Legal & Data Handling Compliance

In accordance with media copyright compliance and intelligence provenance standards, this platform stores **only metadata, extracted factual claims, and brief excerpts with explicit attribution**. It **never** scrapes, stores, or reproduces full article texts.
