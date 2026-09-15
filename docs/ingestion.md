# Dynamic Ingestion Pipeline — Lenny Growth Assistant

## 1. Overview

The ingestion pipeline dynamically fetches, parses, chunks, embeds, and indexes podcast transcripts from the open-source repository `https://github.com/ChatPRD/lennys-podcast-transcripts`.

**Strict Rule**: No proprietary or raw transcript files are committed into this git repository. The system discovers and pulls transcripts dynamically at runtime.

---

## 2. Ingestion Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Dynamic Git Shallow Fetch (HEAD commit discovered)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 2. Idempotency Check (commit_sha + embedding_model)          │
│    - If commit already ingested -> skip cleanly             │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 3. Episode Discovery & Metadata Parsing                     │
│    - Markdown turns: `Speaker (HH:MM:SS): text`             │
│    - Sidecar JSON: guest, youtube_url, duration, keywords   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 4. Speaker-Aware & Timestamp-Aware Chunking                 │
│    - 350-token target / 600-token max / 1-turn overlap      │
│    - Deterministic SHA-256 content hashing                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 5. Batch Vector Embedding via Ollama nomic-embed-text       │
│    - 768-dimensional dense vectors                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ 6. PostgreSQL Upsert & IngestionRun Audit Record            │
│    - Updates `episodes`, `transcript_chunks`, and index      │
│    - Records run status: completed / completed_with_errors   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Idempotency Strategy

1. **Commit-Level Guard**: `IngestionRun` records store `commit_sha` and `embedding_model`. If an identical commit was already indexed with the same model, the run exits early with `skipped`.
2. **Chunk-Level Hash**: Every chunk has a deterministic `content_hash = SHA256(episode_id : chunk_index : content)`.
3. **Atomic Replacement**: When re-indexing an episode, all existing chunks for that `episode_id` are deleted and re-inserted inside a single database transaction.

---

## 4. Running the Ingestion CLI

```bash
# Ingest first 5 episodes (fast smoke test)
python scripts/ingest.py --limit 5

# Force full re-ingestion
python scripts/ingest.py --force

# Custom model or repo
python scripts/ingest.py --model nomic-embed-text
```
