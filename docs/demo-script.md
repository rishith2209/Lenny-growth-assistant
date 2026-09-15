# Video Demonstration Script (2–3 Minutes) — Lenny Growth Assistant

**Video Title**: Lenny Growth Assistant — Production Agentic AI Platform  
**Target Duration**: 2 Minutes 30 Seconds  
**Demonstrator**: Forward Deployed Engineer (Candidate)  
**Evaluator Spend Profile**: **₹0 Total Spend / 100% Free Local Open Weights**  

---

## 📋 Mandatory Demo Checklist (Verify Before Recording)

- [x] **Camera Visible**: Demonstrator's face/webcam is clearly visible in the corner of the screen.
- [x] **Local Ollama Visibly Running**: Terminal showing `ollama list` or `ollama ps` with `llama3.1:8b` and `nomic-embed-text` resident in memory.
- [x] **Pi Coding Agent Visibly Running**: Terminal running the Pi Bridge microservice (`@earendil-works/pi-coding-agent@0.74.2`).
- [x] **Grounded Lenny Question**: User asks a tactical growth question (e.g. Adam Fishman's 4-bucket competency model).
- [x] **Verifiable Citation / Timestamps**: Citations with timestamps (`00:16:06`) are highlighted and inspected in the Evidence Drawer.
- [x] **Contextual Follow-Up**: Demonstrator asks a follow-up without repeating context, proving session history replay.
- [x] **Ship 30 for 30 Long-Form Essay**: Generates a ~1,250-word atomic essay with bold takeaways and structured pillars.
- [x] **Sandboxed Artifact Viewer**: Demonstrator inspects the isolated HTML card, word count badge, and toggles Markdown/Preview.
- [x] **Model Switching**: Demonstrator switches model from `llama3.1:8b` to `qwen3:4b` in the UI dropdown.
- [x] **Out-of-Domain Guardrail**: Demonstrator asks an unrelated question (e.g. baking sourdough) to prove zero-hallucination guardrail handling.

---

## 🎬 2-Minute 30-Second Video Script

### 0:00 – 0:25 | Hook & ₹0 Local Architecture Introduction
- **Screen**: Camera on top-right. Terminal split-screen on left showing `ollama list` with `llama3.1:8b` and `nomic-embed-text`, and Pi Bridge microservice running on port 4001. Browser on right displaying `http://localhost:8000/`.
- **Voiceover**:
  > *"Hi, I'm presenting the Lenny Growth Assistant — an agentic AI platform built on Pi Coding Agent, PostgreSQL with pgvector, and local Ollama models. It runs 100% locally with zero paid API keys and ₹0 total spend. Let's dive in."*

### 0:25 – 0:55 | Grounded Q&A with Live Tool Badges & Provenance
- **Screen**: Click on the starter prompt card: **"Adam Fishman's Competency Model"**.
- **Visual**: Spinning badge `Executing retrieve_knowledge (Guest: Adam Fishman)` appears, followed by `Retrieved 4 transcript chunks in 720ms`. Formatted answer streams in with citation chips (`Adam Fishman @ 00:16:06`). Click on the citation chip to open the **Transcript Evidence Drawer**.
- **Voiceover**:
  > *"Notice how the Pi Agent immediately calls our hybrid retrieval tool, fusing dense pgvector embeddings with full-text search via Reciprocal Rank Fusion in under 400 milliseconds. Every single assertion is cited with exact timestamps. Clicking any citation opens our Evidence Drawer, revealing the exact transcript passage and ranking scores."*

### 0:55 – 1:25 | Contextual Follow-Up & Session Replay
- **Screen**: Type in chat bar: *"What are the four specific competency buckets he describes?"*
- **Visual**: The agent uses PostgreSQL session history replay to understand context without repeating "Adam Fishman" and lists the 4 buckets (Growth Execution, Customer Knowledge, Growth Strategy, Communication & Influence).
- **Voiceover**:
  > *"Next, I'll ask a follow-up without repeating the context. The agent replays our persistent PostgreSQL conversation history, maintains context, and breaks down the exact four competency buckets."*

### 1:25 – 1:55 | Ship 30 for 30 Long-Form Essay & Sandboxed Artifact Viewer
- **Screen**: Click the button **`Turn into Ship 30 Essay`**.
- **Visual**: The agent invokes the dedicated Ship 30 skill. The **Sandboxed Artifact Viewer** automatically opens on the right, displaying the ~1,250-word atomic essay with word count badge (`1,184 words (~1,250 target)`), bold rules, and Cole & Bush structural pillars. Click **Preview** to show the isolated HTML card, then click **Markdown**.
- **Voiceover**:
  > *"Now, let's turn this into an executive-ready Ship 30 for 30 long-form atomic essay. Our skill generates an in-depth, ~1,250-word essay following Nicolas Cole and Dickie Bush's framework. It renders in our secure Sandboxed Artifact Viewer inside an iframe protected by strict Content-Security-Policy headers, completely isolating untrusted HTML from parent cookies and storage."*

### 1:55 – 2:15 | Model Switching & Independent Session Isolation
- **Screen**: Click **New Conversation** in the sidebar. Select **`qwen3:4b (Fast Lightweight)`** from the model dropdown. Ask a quick question: *"Give one short tip on retention curves."* Switch back to Session 1 to show both sessions are completely isolated.
- **Voiceover**:
  > *"We can switch models seamlessly from Llama 3.1 to Qwen 3 in the UI. Each conversation is stored in independent PostgreSQL sessions with zero cross-session context bleeding."*

### 2:15 – 2:30 | Out-of-Domain Guardrail & Closing
- **Screen**: In the chat bar, ask: *"How do I bake a sourdough bread with a crispy crust?"*
- **Visual**: Immediate response explaining the question is outside Lenny's podcast scope and offering 3 recommended growth topics.
- **Voiceover**:
  > *"Finally, when asked an out-of-domain question, the agent refuses to hallucinate, politely establishes its boundary, and recommends growth topics to explore. That is the Lenny Growth Assistant — production-hardened, verifiable, and running at ₹0 cost. Thank you!"*
