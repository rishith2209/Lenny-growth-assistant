"""
Ship 30 for 30 Skill Engine — Lenny Growth Assistant
Encodes Dickie Bush & Nicolas Cole's Ship 30 for 30 atomic essay and long-form framework principles:
1. Specific, high-converting Hook (Headline + Sub-headline + 1-sentence opening)
2. 1 Single Core Idea / North Star Thesis
3. The Context & Stakes (why conventional wisdom fails)
4. 3-5 Modular Framework Pillars (skimmable headings, rhythm, bolding, bullet points)
5. Transcript Grounding & Citations (exact speaker attribution, episode, and timestamps)
6. The Golden Takeaway / Memorable Closing Punchline
7. Target Word Count: ~1,250 words (Tolerance: 1,000 to 1,500 words, 1,250 ± 20%)
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Ship30ValidationResult(BaseModel):
    is_valid: bool
    word_count: int
    target_word_count: int = 1250
    tolerance_min: int = 1000
    tolerance_max: int = 1500
    has_hook: bool
    has_core_idea: bool
    has_subheadings: bool
    has_citations: bool
    citation_count: int
    sections_found: List[str]
    warnings: List[str] = Field(default_factory=list)


SHIP30_SYSTEM_PROMPT = """You are a World-Class Growth Writer and Editor specializing in Nicolas Cole & Dickie Bush's Ship 30 for 30 Framework.
Your mission is to transform Lenny's podcast transcript insights into a masterclass Long-Form Atomic Essay (approx. 1,250 words).

Strict Ship 30 for 30 Structural Rules:
1. HEADLINE & HOOK:
   - Formulate a clear, irresistible headline (e.g. "How [Company/Leader] Mastered [Growth Topic]: The [X]-Step Framework").
   - Sub-headline: 1 sentence summarizing the non-obvious breakthrough.
   - Opening Line: A captivating hook stating the core problem or counter-intuitive reality.

2. ONE CORE IDEA:
   - Identify ONE central thesis. Every paragraph must serve this single thesis. No wandering tangents.

3. THE CONTEXT & STAKES (approx. 150-200 words):
   - Explain why traditional approaches fail and why this insight matters now.

4. 3-5 ACTIONABLE FRAMEWORK PILLARS (approx. 800-900 words total):
   - Use punchy, numbered or descriptive H2/H3 subheadings.
   - Write with high rhythm: mix short punchy sentences with structured bullet points.
   - Use **bold emphasis** on key takeaways and tactical rules.
   - GROUND EVERY PILLAR IN TRANSCRIPT EVIDENCE: Quote or directly attribute insights to the speaker, citing the exact timestamp formatted as [Speaker Name, Episode, MM:SS or HH:MM:SS].

5. THE GOLDEN QUESTION / CLOSING TAKEAWAY (approx. 150 words):
   - End with a punchy synthesis, a reflection question for the reader, or a memorable 1-line rule of thumb.

6. LENGTH REQUIREMENT:
   - Target length: Approximately 1,250 words (1,000 - 1,500 word range). Write in depth with tactical nuance, examples, and detailed operational steps.
"""


def count_words(text: str) -> int:
    """Accurately count words in markdown or plain text."""
    clean = re.sub(r"[#*`_\[\]()>\-:#]", " ", text)
    words = [w for w in clean.split() if any(c.isalnum() for c in w)]
    return len(words)


def extract_citations(text: str) -> List[Dict[str, str]]:
    """Extract transcript citations formatted like [Speaker, Episode, 00:15:30] or (00:15:30)."""
    citations = []
    # Pattern 1: [Speaker, Episode, Timestamp] or [Speaker | Timestamp]
    bracket_pattern = re.findall(r"\[(.*?)\]", text)
    for match in bracket_pattern:
        if any(char.isdigit() for char in match) and (":" in match or "00:" in match):
            citations.append({"raw": match, "type": "bracket"})

    # Pattern 2: Timestamp in parentheses e.g. (00:16:06)
    paren_pattern = re.findall(r"\(([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\)", text)
    for match in paren_pattern:
        citations.append({"raw": match, "type": "timestamp"})

    return citations


def validate_ship30_essay(content: str, tolerance_min: int = 1000, tolerance_max: int = 1500) -> Ship30ValidationResult:
    """Validate that the generated essay adheres to Ship 30 for 30 guidelines."""
    words = count_words(content)
    warnings = []

    # Check word count tolerance
    if words < tolerance_min:
        warnings.append(f"Word count ({words}) is below minimum target ({tolerance_min}).")
    elif words > tolerance_max:
        warnings.append(f"Word count ({words}) exceeds maximum target ({tolerance_max}).")

    # Check for Hook / Headline
    has_hook = bool(re.search(r"^#\s+.+", content, re.MULTILINE))
    if not has_hook:
        warnings.append("Missing primary H1 headline/hook.")

    # Check for Subheadings
    subheadings = re.findall(r"^#{2,3}\s+(.+)", content, re.MULTILINE)
    has_subheadings = len(subheadings) >= 3
    if not has_subheadings:
        warnings.append(f"Found only {len(subheadings)} subheadings; expected at least 3 framework pillars.")

    # Check for Citations
    citations = extract_citations(content)
    has_citations = len(citations) > 0
    if not has_citations:
        warnings.append("No transcript timestamps or speaker citations found in essay content.")

    # Check Core Idea
    has_core_idea = bool(re.search(r"(core idea|thesis|takeaway|framework|rule)", content, re.IGNORECASE))

    is_valid = (words >= (tolerance_min - 150)) and has_hook and len(subheadings) >= 2

    return Ship30ValidationResult(
        is_valid=is_valid,
        word_count=words,
        target_word_count=1250,
        tolerance_min=tolerance_min,
        tolerance_max=tolerance_max,
        has_hook=has_hook,
        has_core_idea=has_core_idea,
        has_subheadings=has_subheadings,
        has_citations=has_citations,
        citation_count=len(citations),
        sections_found=subheadings,
        warnings=warnings,
    )


def generate_atomic_essay_html(
    title: str,
    markdown_content: str,
    guest: Optional[str] = None,
    episode_title: Optional[str] = None,
    word_count: Optional[int] = None,
) -> str:
    """
    Generate a self-contained, responsive, beautifully styled HTML card for the Ship 30 Atomic Essay.
    This HTML is strictly sandboxed in the Artifact Viewer.
    """
    actual_wc = word_count or count_words(markdown_content)

    # Basic markdown formatting conversions for clean HTML display
    formatted_body = markdown_content
    # Escape dangerous raw scripts/tags
    formatted_body = formatted_body.replace("<script>", "&lt;script&gt;").replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")

    # Headers
    formatted_body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", formatted_body, flags=re.MULTILINE)
    formatted_body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", formatted_body, flags=re.MULTILINE)
    formatted_body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", formatted_body, flags=re.MULTILINE)

    # Bold & Italic
    formatted_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted_body)
    formatted_body = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted_body)

    # Citations styling [Speaker, Episode, Timestamp]
    formatted_body = re.sub(
        r"\[(.*?([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?).*?)\]",
        r'<span class="citation-chip"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg>\1</span>',
        formatted_body,
    )

    # Paragraphs
    paragraphs = formatted_body.split("\n\n")
    processed_paragraphs = []
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if p_clean.startswith("<h1") or p_clean.startswith("<h2") or p_clean.startswith("<h3"):
            processed_paragraphs.append(p_clean)
        elif p_clean.startswith("- ") or p_clean.startswith("* "):
            items = [f"<li>{line[2:].strip()}</li>" for line in p_clean.split("\n") if line.startswith(("- ", "* "))]
            processed_paragraphs.append(f"<ul>{''.join(items)}</ul>")
        elif re.match(r"^\d+\.\s", p_clean):
            items = [f"<li>{re.sub(r'^\d+\.\s*', '', line).strip()}</li>" for line in p_clean.split("\n") if re.match(r"^\d+\.\s", line)]
            processed_paragraphs.append(f"<ol>{''.join(items)}</ol>")
        else:
            # Regular paragraph
            processed_paragraphs.append(f"<p>{p_clean.replace(chr(10), '<br/>')}</p>")

    html_content = "\n".join(processed_paragraphs)

    guest_badge = f'<span class="meta-tag guest-tag">👤 {guest}</span>' if guest else ""
    ep_badge = f'<span class="meta-tag ep-tag">🎙️ {episode_title}</span>' if episode_title else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --accent-glow: rgba(88, 166, 255, 0.15);
      --citation-bg: #1f2937;
      --citation-border: #374151;
      --citation-text: #60a5fa;
      --success: #3fb950;
      --tag-bg: #21262d;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.7;
      padding: 24px 16px;
      display: flex;
      justify-content: center;
    }}
    .essay-card {{
      max-width: 820px;
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }}
    .essay-header {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}
    .framework-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--accent-glow);
      color: var(--accent);
      border: 1px solid rgba(88, 166, 255, 0.3);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 16px;
    }}
    .meta-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
      align-items: center;
    }}
    .meta-tag {{
      background: var(--tag-bg);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .wc-tag {{
      color: var(--success);
      font-weight: 600;
    }}
    h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      color: var(--text-bright);
      line-height: 1.3;
      margin-bottom: 12px;
      letter-spacing: -0.02em;
    }}
    h2 {{
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--text-bright);
      margin: 32px 0 14px 0;
      border-left: 3px solid var(--accent);
      padding-left: 12px;
    }}
    h3 {{
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-bright);
      margin: 20px 0 10px 0;
    }}
    p {{
      margin-bottom: 18px;
      font-size: 1.02rem;
    }}
    strong {{
      color: var(--text-bright);
      font-weight: 600;
    }}
    ul, ol {{
      margin: 16px 0 24px 24px;
    }}
    li {{
      margin-bottom: 10px;
      padding-left: 4px;
    }}
    .citation-chip {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: var(--citation-bg);
      border: 1px solid var(--citation-border);
      color: var(--citation-text);
      font-size: 0.8rem;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      padding: 2px 8px;
      border-radius: 4px;
      margin: 0 4px;
      vertical-align: middle;
      font-weight: 500;
    }}
    .footer-note {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      font-size: 0.82rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
  </style>
</head>
<body>
  <article class="essay-card">
    <header class="essay-header">
      <div class="framework-badge">⚡ Ship 30 for 30 Atomic Essay</div>
      <div class="meta-bar">
        <span class="meta-tag wc-tag">📊 ~{actual_wc} Words</span>
        {guest_badge}
        {ep_badge}
      </div>
    </header>
    <main class="essay-body">
      {html_content}
    </main>
    <footer class="footer-note">
      <span>Grounded in Lenny's Podcast Transcripts</span>
      <span>Framework: Ship 30 for 30 (Cole & Bush)</span>
    </footer>
  </article>
</body>
</html>
"""
