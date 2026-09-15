# Manual UI & Evaluator Test Plan — Lenny Growth Assistant

**Target Audience**: Take-Home Evaluator / Senior Engineering Reviewer  
**Total Evaluation Time**: ~3–5 Minutes  
**Prerequisites**: Services running locally via `http://localhost:8000` (or `http://localhost:5173`)  
**Cost**: **₹0 / Local Open Weights**  

---

## 1. Quickstart Launch (If starting from scratch)

```bash
# 1. Start PostgreSQL + pgvector
docker-compose up -d postgres

# 2. Start Pi Bridge
cd apps/pi-bridge && npm install && npm run build && npm start

# 3. Start FastAPI Backend & Frontend (Unified on Port 8000)
# (In project root with virtualenv active)
PYTHONPATH=. uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000/`** in your browser.

---

## 2. Step-by-Step Evaluator Script

### Step 1: Immediate Verification of Brand & Model Status (First 15s)
1. Observe the top left sidebar: **"Lenny Assistant — Growth Knowledge Agent"**.
2. Check the model dropdown at the bottom of the sidebar: shows **`llama3.1:8b (Primary)`**.
3. Check the status badge: **`pgvector Active`** with a green dot and **`₹0 Spend`** pill badge.
4. Check the top header: shows active session title, model badge, and **`Grounded RAG`** shield indicator.

*Expected Result*: Clean dark slate/indigo UI with zero console errors.

---

### Step 2: Grounded Q&A with Live Tool Indicators & Citations (Minute 1)
1. In the welcome screen, click on the starter card: **"Adam Fishman's Competency Model"** (or type *"What advice does Adam Fishman give regarding growth teams?"* in the input box).
2. Observe the streaming lifecycle:
   - Spinning badge: `Executing retrieve_knowledge (Guest: Adam Fishman)`
   - Green badge: `Retrieved 4 transcript chunks in ~700ms`
   - Real-time token streaming with formatted Markdown and numbered sections.
3. Observe the generated citations at the bottom of the response:
   - Interactive citation chips like `Adam Fishman (00:16:06)`.

*Expected Result*: Grounded response synthesizing the 4 competency buckets (Growth Execution, Customer Knowledge, Growth Strategy, Communication & Influence) with exact transcript citations.

---

### Step 3: Deep Provenance Inspection (Minute 2)
1. Click on one of the citation chips (e.g. `Adam Fishman (00:16:06)`).
2. The **Transcript Evidence Drawer** slides out from the right side of the screen.
3. Review the exact raw quote from the episode transcript, the speaker attribution, and the cosine similarity / RRF ranking scores.

*Expected Result*: Direct verification of the AI's claims against the underlying transcript text.

---

### Step 4: One-Click Ship 30 for 30 Long-Form Atomic Essay (Minute 3)
1. At the bottom of the assistant message, click the pill button: **`Turn into Ship 30 Essay`**.
2. The agent executes the dedicated Ship 30 skill, synthesizing an in-depth long-form atomic essay (~1,250 words) structured around:
   - Clear headline & hook
   - One core idea
   - Context & stakes
   - 3–5 actionable framework pillars with bold rules and citations
   - Memorable closing takeaway
3. Upon completion, the **Sandboxed Artifact Viewer** automatically opens in the right pane.
4. Review:
   - Word count badge: `~1,250 words target (1,000–1,500 tolerance)`
   - Toggle between **Preview** (isolated styled HTML card) and **Markdown** (raw Markdown text).
   - Click **Copy Markdown** or **Download HTML** to verify export capabilities.

*Expected Result*: Standalone sandboxed HTML artifact rendered with rich typography, strictly isolated inside an `<iframe>` with `Content-Security-Policy: default-src 'none'`.

---

### Step 5: Contextual Multi-Turn Follow-Up (Minute 4)
1. In the chat bar, ask a follow-up question referencing the conversation context:
   - *"What are the four specific competency buckets he describes?"*
2. Notice you did not repeat "Adam Fishman" or "growth competency model".
3. The agent utilizes the PostgreSQL session history replay to understand the context and immediately answers with the four buckets.

*Expected Result*: Coherent, context-aware answer proving persistent session memory.

---

### Step 6: Out-of-Domain Guardrail Verification (Minute 5)
1. Ask an unrelated question:
   - *"How do I bake a sourdough bread with a crispy crust?"*
2. Observe the immediate response:
   - The agent refuses to hallucinate and explains that the question falls outside the scope of **Lenny's Podcast archive**.
   - It offers 3 actionable growth alternative topics to explore instead (e.g. PMF milestones, growth loops, pricing & packaging).

*Expected Result*: Zero hallucination, clear boundary enforcement, and polite guidance back to domain expertise.

---

### Step 7: Independent Session Isolation & Model Switching
1. Click **New Conversation** in the sidebar.
2. Select **`qwen3:4b (Fast Lightweight)`** from the model dropdown.
3. Type: *"Give one short tip on retention curves."*
4. Switch back to the first session in the sidebar.
5. Verify that Conversation 1 has all previous messages intact and Conversation 2 has only its own messages.

*Expected Result*: Complete state isolation with zero cross-session context leakage.
