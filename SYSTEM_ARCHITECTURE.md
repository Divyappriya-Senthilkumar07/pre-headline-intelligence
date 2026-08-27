# Pre-Headline Intelligence — System Architecture & Production Specifications

## 1. System Philosophy & Core Product Principle

> **"We don't just detect a story is emerging — we prove it, before it's obvious, in the language it's actually forming in."**

Pre-Headline Intelligence is a **Story Formation Intelligence / Narrative Provenance Platform**. It is not a generic news aggregator, reader, or summarizer.

---

## 2. End-to-End Pipeline Architecture

```
[ INGESTION SUBSYSTEM ]
 Analyst Uploads (PDF, Images, Audio, Video, Text)
 RSS Feeds (Periodic & On-Demand)
 GDELT GKG (Global Knowledge Graph Events)
 URL Scraping & Document Fetching
        ↓
[ AGENT 1: Ingestion & Normalization ]
 - SHA-256 Deduplication & Canonicalization
 - Media Extractors (OCR, Text, Audio, Metadata)
 - Excerpt-Only Storage (Attribution, Legal compliance)
        ↓
[ AGENT 2: Context Extraction ]
 - Multilingual NER (Indic & English Entities)
 - Semantic Relevance Filtering (Zero hallucination)
 - Media Event Graph Node Normalization
        ↓
[ AGENT 3: Expansion & Vectorization ]
 - 384-Dimensional Multilingual Sentence Embeddings
 - Bounded Graph Traversal & Entity Linking
        ↓
[ AGENT 4: Story Clustering ]
 - Cross-Language Density-Based HDBSCAN Clustering
 - Adaptive Distance Thresholds (0.42 Cosine Distance)
 - Cluster Purity & Multi-Language Fusion
        ↓
[ AGENT 5: Independence & Corroboration ]
 - Publisher Ownership Tree Resolution
 - Syndication & Wire Copy Fingerprinting
 - Genuinely Independent Desk Count (Separated from Raw Article Count)
 - Contradiction Detection (Cross-Claim Verification)
        ↓
[ HARD CONTRADICTION GATE ]
 ⚠️ If load-bearing contradiction is active → HALT PREDICTION & BLOCK ALERTS
        ↓
[ AGENT 6: Narrative & Formation Scoring ]
 - 6-Dimension Explainable Scoring:
   1. Source Diversity (25%)
   2. Temporal Spread (15%)
   3. Entity Alignment (20%)
   4. Cross-Language Corroboration (20%)
   5. Evidence Strength (10%)
   6. Independence Quality (10%)
        ↓
[ AGENT 7: Prediction & Trajectory Projection ]
 - Probability vs. Impact STRICTLY SEPARATED
 - 4 Trajectory Stages: LOCAL → REGIONAL → NATIONAL → MAINSTREAM
 - Historical Precursor Calibration
        ↓
[ AGENT 8: Evidence Chain & Grounded Copilot ]
 - Immutable Structured Provenance Chain (Source → Claim → Corroboration → Confidence)
 - Grounded Analyst Copilot (Story-scoped retrieval, Strict negative refusal rule)
        ↓
[ AGENT 9: Alert Orchestrator & Delivery ]
 - Urgency × Probability × Impact Ranking Score
 - Defense-in-Depth Gate Enforcement
 - Lifecycle States: ACTIVE → INVESTIGATING → ACKNOWLEDGED → DISMISSED → BLOCKED
        ↓
[ EVALUATION & REPLAY SUBSYSTEM ]
 - Deterministic Step-by-Step Historical Replay
 - Zero Look-Ahead Bias Guarantee
 - Ground-Truth Lead-Time Benchmarking
```

---

## 3. Core Database Models & Indexing

| Table | Primary Key | Critical Indexes | Cascade Behavior |
| :--- | :--- | :--- | :--- |
| `stories` | `id` (UUID) | `status`, `formation_score`, `formation_status`, `independence_score`, `contradiction_status` | Parent cluster; cascades to notes & joins |
| `articles` | `id` (UUID) | `source_id`, `url` (UNIQUE), `published_at`, `language` | Restricted on source deletion |
| `sources` | `id` (UUID) | `domain`, `is_active` | Parent for articles |
| `claims` | `id` (UUID) | `article_id`, `created_at` | Cascades on article delete |
| `contradictions`| `id` (UUID) | `story_id`, `is_load_bearing`, `status` | Cascades on story delete |
| `predictions` | `id` (UUID) | `story_id`, `prediction_status`, `formation_probability` | Cascades on story delete |
| `evidence_chains`| `id` (UUID)| `story_id`, `chain_status` | Cascades on story delete |
| `alerts` | `id` (UUID) | `story_id`, `status`, `ranking_score` | Cascades on story delete |
| `story_notes` | `id` (UUID) | `story_id`, `created_at` | Cascades on story delete |
| `watchlists` | `id` (UUID) | `user_id`, `is_active` | User-scoped |
| `replay_scenarios`| `id` (String)| `scenario_type` | Fixture-based |
| `replay_snapshots`| `id` (UUID)| `scenario_id`, `event_order`, `replay_timestamp` | Cascades on scenario delete |
| `evaluation_runs` | `id` (UUID)| `dataset_version`, `status`, `started_at` | Versioned benchmark run |

---

## 4. Security & Hardening Architecture

1. **Zero Secret Leakage**:
   - Secrets managed via environment variables (`.env`).
   - Logging middleware masks sensitive data and suppresses credentials.
2. **Media Pipeline Hardening**:
   - File size ceiling: $50\text{ MB}$ (configurable).
   - Filename sanitization: Directory traversal (`../`) stripped; stored under randomized UUIDs.
   - Whitelist enforcement for MIME types and extensions.
   - Processing failures result in visible `FAILED` status with exact error reasons — never fabricated content.
3. **Prompt Injection & Copilot Defenses**:
   - Ingested text is wrapped in data delimiters and treated as untrusted payload.
   - Copilot enforces negative refusal rule on ungrounded queries or instruction override attempts.
   - Copilot caches are keyed by `story_id`, `evidence_hash`, and query to ensure zero cross-story leakage.
4. **Hard Contradiction Gate**:
   - When a load-bearing contradiction is active, prediction and alerting are unconditionally blocked across all entry points: Prediction Agent, Alert Orchestrator, API routes, Historical Replay, and Evaluation Engine.
5. **Observability & Request Tracing**:
   - `X-Request-ID` attached to all requests and forwarded through structured logs.
   - `GET /health/live` (process health) and `GET /health/ready` (database connection verification).
