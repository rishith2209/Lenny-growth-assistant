# API Contracts — Lenny Growth Assistant (M1)

## 1. REST Endpoints (FastAPI Backend)

### `GET /health`
Returns overall system status, PostgreSQL connectivity, and provider readiness.
```json
{
  "status": "healthy",
  "environment": "development",
  "database": {
    "status": "healthy",
    "connected": true,
    "pgvector_installed": true
  },
  "providers": {
    "primary_provider": "ollama",
    "providers": {
      "ollama": {
        "status": "healthy",
        "models_available": ["llama3.1:8b", "qwen3:8b", "qwen3:4b", "nomic-embed-text"],
        "embedding_model_available": true
      },
      "anthropic": {
        "status": "unavailable",
        "details": { "reason": "No ANTHROPIC_API_KEY configured (optional provider)" }
      }
    }
  },
  "cost_profile": "100% Free / ₹0 spend"
}
```

---

### `POST /api/v1/knowledge/search`
Executes hybrid vector + full-text search.

**Request**:
```json
{
  "query": "What are the best metrics for SaaS retention?",
  "top_k": 5,
  "filters": {
    "guest": "Elena Verna"
  }
}
```

**Response**:
```json
{
  "query": "What are the best metrics for SaaS retention?",
  "total_results": 5,
  "confidence_score": 0.82,
  "confidence_tier": "high",
  "execution_time_ms": 38,
  "results": [
    {
      "chunk_id": "ep_elena_verna_0012",
      "episode_id": "ep_elena_verna",
      "episode_title": "Elena Verna on B2B Product-Led Growth",
      "guest": "Elena Verna",
      "speaker": "Elena Verna",
      "timestamp_formatted": "18:45",
      "start_time_seconds": 1125.0,
      "end_time_seconds": 1190.0,
      "content": "Elena Verna (18:45): When assessing retention, cohort curves after month 3 are the truest indicator...",
      "provenance": {
        "chunk_id": "ep_elena_verna_0012",
        "episode_id": "ep_elena_verna",
        "episode_title": "Elena Verna on B2B Product-Led Growth",
        "guest": "Elena Verna",
        "start_time_seconds": 1125.0,
        "end_time_seconds": 1190.0,
        "timestamp_formatted": "18:45",
        "youtube_url": "https://youtube.com/watch?v=...",
        "source_commit": "be8ab89...",
        "speaker": "Elena Verna"
      },
      "semantic_score": 0.845,
      "lexical_score": 0.720,
      "rrf_score": 0.0312
    }
  ]
}
```

---

### `POST /api/v1/sessions`
Creates a durable chat session in PostgreSQL.

**Request**:
```json
{
  "title": "PLG Strategy Discussion",
  "provider": "ollama",
  "model": "llama3.1:8b",
  "user_metadata": { "role": "founder" }
}
```

---

## 2. Server-Sent Events Contract (`POST /internal/agent/run`)

The Pi Bridge service streams real-time SSE deltas and tool execution lifecycle events:

```
event: data
data: {"event_id":"evt_1","session_id":"conv_123","timestamp":"2026-09-14T...","type":"agent_started","model":"llama3.1:8b","provider":"ollama"}

event: data
data: {"event_id":"evt_2","session_id":"conv_123","timestamp":"2026-09-14T...","type":"tool_started","tool_call_id":"call_99","tool_name":"retrieve_knowledge_test","arguments":{"query":"product-market fit"}}

event: data
data: {"event_id":"evt_3","session_id":"conv_123","timestamp":"2026-09-14T...","type":"tool_result","tool_call_id":"call_99","tool_name":"retrieve_knowledge_test","result":{"total_results":3,"results":[...]}}

event: data
data: {"event_id":"evt_4","session_id":"conv_123","timestamp":"2026-09-14T...","type":"text_delta","delta":"According to Andy Johns on Lenny's Podcast..."}

event: data
data: {"event_id":"evt_5","session_id":"conv_123","timestamp":"2026-09-14T...","type":"agent_completed","latency_ms":3120,"cost_inr":0.0}
```
