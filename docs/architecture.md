# Pre-Headline Intelligence — Architecture Specification

## 1. System Philosophy & Differentiators

Pre-Headline Intelligence is an intelligence provenance and story formation platform designed to detect, corroborate, and prove emerging narratives before they appear as mainstream headlines.

```
       [Raw Fragment Signals]
                 ↓
      [Context & Entity Graph]
                 ↓
    [Multilingual Clustering]
                 ↓
[Independence & Contradiction Gate]
                 ↓
    [Story Formation Scoring]
                 ↓
     [Trajectory & Impact]
                 ↓
      [Early Intelligence]
```

### The Three Pillars

1. **Independent-Source Corroboration**: Distinguishing syndication chains ($A \rightarrow B \rightarrow C$) from genuine multi-source convergence ($A, B, C$).
2. **Mandatory Evidence Chain**: Every alert requires a click-through evidence graph: $\text{Source} \rightarrow \text{Claim} \rightarrow \text{Evidence} \rightarrow \text{Corroboration} \rightarrow \text{Confidence}$.
3. **Contradiction Gate**: A hard stop in code. Conflicting load-bearing claims immediately halt predictions and alert emission.

---

## 2. Media Event Graph (PostgreSQL Adjacency List)

Graph edges are modeled in PostgreSQL using the `graph_edges` table:

- **Nodes**: `Entity`, `Event`, `Source`, `Claim`, `Article`
- **Edges**:
  - Standard: `works_for`, `investigated_by`, `issued`, `reported`, `affiliated_with`
  - Proprietary: `independence`, `contradiction`, `claim_evidence`, `corroborates`

---

## 3. The 9 Modular Agents

1. **Agent 1 — Discovery**: Ingests candidate signals from RSS, GDELT, and licensed APIs.
2. **Agent 2 — Context**: Resolves keyword collisions and extracts confirmed entity links.
3. **Agent 3 — Expansion**: Discovers outward graph paths (regulators, documents, related entities).
4. **Agent 4 — Story Clustering**: Groups related articles using multilingual embeddings + HDBSCAN.
5. **Agent 5 — Independence & Corroboration**: Scores source independence and detects claim conflicts.
6. **Agent 6 — Narrative & Formation**: Computes the 6-dimension Story Formation Score.
7. **Agent 7 — Prediction**: Projects trajectory and the Probability × Impact matrix.
8. **Agent 8 — Evidence & Investigation**: Assembles evidence chains and powers the grounded copilot.
9. **Agent 9 — Alert Orchestrator**: Ranks alerts and enforces the Contradiction Gate guard clause.
