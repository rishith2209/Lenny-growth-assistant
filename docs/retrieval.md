# Hybrid Retrieval & Ranking Engine (RRF)

## 1. Retrieval Strategy

The Lenny Growth Assistant utilizes a two-stage hybrid retrieval architecture combining dense semantic vector search with sparse lexical full-text search, fused using **Reciprocal Rank Fusion (RRF)**.

```
Query
  ├── (1) Semantic Search (pgvector cosine similarity: `<=>`)
  │     - Model: `nomic-embed-text` (768-dim)
  │     - Index: HNSW (m=16, ef_construction=64)
  │
  └── (2) Lexical Search (PostgreSQL full-text: `tsvector` @@ `plainto_tsquery`)
        - Index: GIN on English dictionary tsvector
        - Ranking: `ts_rank_cd`
        │
        ▼
   Reciprocal Rank Fusion (RRF)
   Score(d) = Σ [ 1 / (60 + Rank_i(d)) ]
        │
        ▼
   Evidence Confidence Scoring + Provenance Citations
```

---

## 2. Reciprocal Rank Fusion (RRF) Formulation

Given a candidate chunk $d$ appearing in ranked lists from semantic and lexical retrieval:

$$RRF(d) = \sum_{m \in \{semantic, lexical\}} \frac{1}{k + \text{rank}_m(d)}$$

Where constant $k = 60$ (standard robust baseline). Chunks appearing at top positions across both semantic and lexical queries receive dominant rank boosts.

---

## 3. Evidence Confidence Heuristic

Rather than using an arbitrary threshold like "at least two chunks", the confidence heuristic combines:
1. **Top Cosine Similarity**: Evaluates raw semantic alignment.
2. **Rank Agreement**: Evaluates whether dense and sparse search agree on top candidates.
3. **Score Separation**: Measures distance between top result and background noise.

### Confidence Tiers
- **`high` ($\ge 0.70$)**: Strong multi-signal match; high certainty.
- **`medium` ($0.45 - 0.69$)**: Moderate match; suitable for standard grounded response.
- **`low` ($0.25 - 0.44$)**: Weak match; response should caveat findings.
- **`unsupported` ($< 0.25$)**: Insufficient evidence in the corpus; triggers out-of-domain handler.

---

## 4. Citation Provenance Contract

Every returned chunk preserves complete citation metadata:
```json
{
  "chunk_id": "ep_andy_johns_0004",
  "episode_id": "ep_andy_johns",
  "episode_title": "Andy Johns on Growth Frameworks",
  "guest": "Andy Johns",
  "speaker": "Andy Johns",
  "timestamp_formatted": "14:22",
  "start_time_seconds": 862.0,
  "end_time_seconds": 915.0,
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "source_commit": "be8ab89a..."
}
```
