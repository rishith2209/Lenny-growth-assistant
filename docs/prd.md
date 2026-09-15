# Product Requirements Document (PRD) — Lenny Growth Assistant

**Project Title**: Lenny Growth Assistant  
**Author**: Forward Deployed Engineer (Candidate)  
**Target User**: Product Managers, Growth Leaders, Founders, and Engineering Evaluators  
**Version**: 1.0.0 (Production Release)  
**Spend Profile**: **₹0 Total Spend / 100% Free Open Weights**  

---

## 1. Problem Statement

Lenny Rachitsky's podcast contains over 300+ interviews with world-class product leaders, growth practitioners, and founders (e.g., Brian Balfour, Elena Verna, Casey Winters, Adam Fishman, Mark Roberge). While this archive is the gold standard for tactical product strategy, accessing and synthesizing specific advice across hours of unstructured audio transcripts is painfully slow.

Generic commercial chatbots (ChatGPT, Claude) suffer from:
1. **Hallucination**: Confidently fabricating growth frameworks not spoken by the guest.
2. **Lack of Provenance**: Inability to link claims back to exact timestamps or transcript passages.
3. **Unstructured Output**: Generating generic bullet points rather than executive-ready, publishing-grade frameworks like Ship 30 for 30 atomic essays.
4. **Cost & Privacy**: Requiring expensive per-token API subscriptions.

---

## 2. Product Objectives & Target Personas

### 2.1 Target Personas
1. **The Head of Growth / Product Leader**: Needs tactical answers on retention loops, PMF indicators, pricing models, and team competency matrices with verified citations to present to their leadership team.
2. **The Growth Writer / Founder**: Needs to turn podcast insights into high-impact, skimmable Ship 30 for 30 long-form atomic essays (~1,250 words) for team memos or public thought leadership.
3. **The Engineering Evaluator**: Needs a robust, self-contained, ₹0-cost architecture running on local open weights (Ollama) that proves end-to-end agentic workflow, hybrid search, resilience, and security.

### 2.2 Core Product Goals
- **Grounded Intelligence**: 100% of factual assertions must originate from indexed transcript chunks with verifiable speaker attribution and timestamps (`MM:SS`).
- **First 30 Seconds "Wow" Factor**: The UI must instantly demonstrate that this is a specialized grounded agent, not a generic LLM wrapper.
- **Dedicated Ship 30 for 30 Skill**: Generate publishing-grade, ~1,250-word atomic essays with structured headings, rhythm, bold takeaways, and isolated HTML card rendering.
- **Zero-Cost & Local Default**: Offline execution on standard 16 GB hardware using Ollama and Pi Coding Agent.

---

## 3. Key Feature Specifications

### 3.1 Conversational Agentic Workflow
- **Multi-Turn Context Replay**: Maintains persistent conversation history in PostgreSQL so users can ask follow-up questions referencing previous answers without repeating context.
- **Interactive Tool Execution Badges**: Real-time visualization of tool execution (`retrieve_knowledge`, `save_artifact`) with execution latency and chunk count indicators.
- **Streaming Token Deltas**: Real-time SSE streaming for instant feedback (<4s time-to-first-token on CPU).

### 3.2 Hybrid Search & Provenance
- **Dense + Sparse Fusion**: Dense vector search (768-dim `nomic-embed-text` with pgvector HNSW index) + English full-text search (PostgreSQL `tsvector` with GIN index) fused via Reciprocal Rank Fusion (RRF, $k=60$).
- **Interactive Citation Chips**: Every assistant response renders clickable speaker/timestamp chips.
- **Slide-out Evidence Drawer**: Clicking any citation opens a slide-out drawer displaying the raw transcript passage, speaker, episode metadata, and cosine/RRF similarity scores.

### 3.3 Ship 30 for 30 Skill Engine & Sandboxed Artifact Viewer
- **Framework Compliance**: Encodes Nicolas Cole & Dickie Bush principles:
  - Strong Headline & Hook
  - Single Core Idea
  - Context & Stakes (why conventional approaches fail)
  - 3–5 Modular Actionable Pillars with exact transcript citations
  - Bold Rules and Memorable Closing Golden Takeaway
- **Word Count Target**: Calibrated to ~1,250 words ($1,000 - 1,500$ words tolerance, $\pm 20\%$).
- **Multi-Layer Sandboxed Viewer**:
  - Split-view toggle between **Markdown View** and **Isolated Rendered Preview**.
  - Rendered inside an `<iframe sandbox="allow-scripts">` backed by strict HTTP `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; img-src data:;` headers.
  - Export tools: Copy Markdown and Download Standalone HTML.

### 3.4 Domain Guardrails & Unsupported Question Handling
- **Out-of-Domain Interception**: Questions regarding cooking, automotive repair, physics, general coding, or prompt injections are intercepted without hallucination.
- **Actionable Guidance**: The agent politely clarifies its focus on Lenny's Podcast archive and presents 3 recommended growth topics to explore.

### 3.5 Model & Provider Management
- **Local Model Switching**: Switch dynamically between `llama3.1:8b` (Primary), `qwen3:4b` (Fast Lightweight), and `qwen3:8b` (Analytical) via the sidebar dropdown.
- **Optional Cloud Provider Adapter**: Fully implemented adapter for Anthropic / OpenAI that activates only when valid API keys are supplied in `.env`.

---

## 4. Non-Functional Requirements

- **Performance**: Time-to-first-token <4s (warm) on local CPU; retrieval latency <400ms.
- **Reliability & Durability**: User messages committed to PostgreSQL before agent execution; interrupted streams persisted with `status: interrupted`.
- **Security**: Zero raw transcript text committed to git; zero secrets committed; strict iframe sandboxing and Content-Security-Policy.
- **Compatibility**: Runs seamlessly on Windows 11 / WSL2 / Linux / macOS.
