# Design System & UI/UX Specification — Lenny Growth Assistant

**Project**: Lenny Growth Assistant  
**Design Framework**: Bespoke Vanilla CSS Design System with Modern Dark Slate/Indigo Theme  
**Typography**: Google Font **Inter** (Interface) + **JetBrains Mono** (Code & Timestamps)  
**Layout Model**: Split-Pane Responsive Layout (Sidebar + Chat Area + Sandboxed Artifact Viewer / Evidence Drawer)  

---

## 1. Visual Hierarchy & Design Philosophy

The Lenny Growth Assistant interface is crafted to provide a state-of-the-art, high-density desktop experience inspired by modern developer platforms (Linear, Raycast, GitHub Next). The goal is to make the product feel extremely responsive, premium, and visually striking from the first second.

### 1.1 Core Design Principles
1. **Grounded Transparency First**: Never hide how the agent came up with an answer. Tool executions, chunk counts, retrieval latencies, and citations are rendered as first-class visual elements.
2. **High-Contrast Dark Aesthetics**: Deep slate backgrounds (`#0a0d14`), subtle borders (`rgba(255, 255, 255, 0.08)`), and vibrant indigo/violet glowing accents (`#6366f1`) ensure readability and focus.
3. **Micro-Interactions & State Clarity**: Smooth hover lifts on starter cards, spinning indicator dots on active tool calls, glowing borders on focused inputs, and animated typing indicators.
4. **Isolated Sandboxing for Generated Media**: Generated HTML essays are visually styled like executive briefing cards with customized headers, metadata badges, and clean typographic rhythm.

---

## 2. Color Palette & Design Tokens

```css
:root {
  /* Background Layers */
  --bg-base: #0a0d14;          /* Deepest canvas */
  --bg-surface: #111622;       /* Sidebars, cards, headers */
  --bg-surface-hover: #182030; /* Interactive hover */
  --bg-surface-active: #1f2a3f;/* Selected session / card */
  --bg-glass: rgba(17, 22, 34, 0.75); /* Backdrop blur header */
  --bg-input: #0d121c;         /* Form inputs & drawers */

  /* Brand Accents */
  --accent-primary: #6366f1;   /* Indigo base */
  --accent-hover: #4f46e5;     /* Darker indigo */
  --accent-light: #818cf8;     /* Light indigo text & chips */
  --accent-glow: rgba(99, 102, 241, 0.25); /* Glow shadow */
  --accent-subtle: rgba(99, 102, 241, 0.12); /* Badge background */

  /* Semantic Feedback */
  --emerald-success: #10b981;  /* RAG active, pgvector connected */
  --emerald-subtle: rgba(16, 185, 129, 0.15);
  --amber-warning: #f59e0b;    /* Word count alerts */
  --rose-danger: #ef4444;      /* Errors, delete actions */

  /* Typography */
  --text-primary: #f8fafc;     /* Main text */
  --text-secondary: #cbd5e1;   /* Sub-text, message body */
  --text-muted: #64748b;       /* Metadata, timestamps */

  /* Borders & Shadows */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-focus: rgba(99, 102, 241, 0.5);
  --shadow-lg: 0 10px 30px rgba(0, 0, 0, 0.6);
}
```

---

## 3. Component Architecture & User Experience

```
+-----------------------------------------------------------------------------------------------+
| Top Header: Active Session Title | Model: llama3.1:8b | Grounded RAG Shield | Toggle Artifacts |
+------------------+----------------------------------------------------+-----------------------+
| Sidebar          | Chat Area                                          | Artifact Viewer /     |
| - Logo & Brand   | - Welcome Hero (4 Curated Starter Cards)           | Evidence Drawer       |
| - New Chat Button| - Assistant Message with formatted Markdown        | (Tabbed Split Pane)   |
| - Session List   | - Inline Tool Badges [Executing retrieve_knowledge]| - Word Count Badge    |
| - Model Selector | - Interactive Citation Chips [Adam Fishman 00:16]  | - Preview (Iframe)    |
|   (llama / qwen) | - Quick Action Button: "Turn into Ship 30 Essay"   | - Raw Markdown View   |
| - pgvector Status| - Floating Input Bar with Submit Button            | - Copy / Download     |
| - ₹0 Spend Badge |                                                    | - Strict CSP Sandbox  |
+------------------+----------------------------------------------------+-----------------------+
```

### 3.1 Key UI Views & States
1. **Welcome View (Zero-State)**: Displays a central title *"What growth challenge are you solving today?"* with 4 quick-launch cards.
2. **Active Streaming State**: Displays a spinning badge with tool arguments, real-time token streaming with smooth cursor tracking, and inline citations.
3. **Slide-Out Evidence Drawer**: Reveals exact podcast transcript excerpts, speaker badges, timestamps, and cosine/RRF similarity scores.
4. **Sandboxed Artifact Viewer**: Embedded `<iframe sandbox="allow-scripts">` rendering publishing-grade standalone HTML atomic essays with word count tolerance indicators.

---

## 4. Accessibility & Responsiveness

- **Keyboard Navigation**: Pressing `Enter` in the chat input sends the message; `Shift+Enter` inserts a newline.
- **High-Contrast Readability**: Text contrast ratios exceed WCAG AA standards (7:1 for primary text on dark surface).
- **Responsive Flex Layout**: Smooth transitions between 1-column mobile view, 2-column chat view, and 3-column split-pane artifact view.
