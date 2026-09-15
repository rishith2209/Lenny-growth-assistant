"""
Domain Guardrail and Unsupported Query Engine — Lenny Growth Assistant
Detects out-of-domain queries, weak retrieval evidence, and formats graceful disclaimers
with actionable growth topic recommendations.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


OUT_OF_DOMAIN_PATTERNS = [
    r"\b(bake|recipe|cook|sourdough|bread|pizza|cake)\b",
    r"\b(car engine|oil change|transmission|brakes|tire pressure)\b",
    r"\b(quantum physics|black hole|string theory|thermodynamics)\b",
    r"\b(weather forecast|rain tomorrow|temperature in)\b",
    r"\b(medical advice|symptoms of|cure for|prescribe)\b",
    r"\b(python syntax|c\+\+ compiler|write a binary search tree|fork\(\)|translate .* into python|write code)\b",
    r"\b(ignore (all|previous) instructions|you are now dan|jailbreak|system override|dump .* passwords|sql injection|hack|bypass security)\b",
]

RECOMMENDED_GROWTH_TOPICS = [
    "Product-Market Fit (PMF) milestones and retention curves (e.g. Casey Winters, Brian Balfour)",
    "Growth Loops vs. Traditional Funnels (e.g. Elena Verna, Dan Hockenmaier)",
    "B2B Sales-Led and Product-Led Growth hybrids (e.g. Mark Roberge, Pete Kazanjy)",
    "Pricing & Packaging optimization strategies (e.g. Madhavan Ramanujam, Patrick Campbell)",
    "Growth team hiring and competency matrices (e.g. Adam Fishman, Hila Qu)",
]


class GuardrailCheckResult(BaseModel):
    is_supported: bool
    reason: Optional[str] = None
    suggested_response: Optional[str] = None
    alternative_topics: List[str] = RECOMMENDED_GROWTH_TOPICS


def check_query_domain(query: str) -> GuardrailCheckResult:
    """Check if query is blatantly out of domain before retrieval."""
    import re
    query_lower = query.lower().strip()

    for pattern in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pattern, query_lower):
            return GuardrailCheckResult(
                is_supported=False,
                reason="OUT_OF_DOMAIN",
                suggested_response=(
                    "I cannot answer this question because it falls outside the scope of **Lenny's Podcast archive**.\n\n"
                    "I specialize exclusively in product management, growth strategy, scaling startups, and leadership insights "
                    "from over 300+ interviews with top founders, PMs, and growth executives.\n\n"
                    "Here are a few topics from the archive you might explore instead:\n"
                    + "\n".join([f"- {topic}" for topic in RECOMMENDED_GROWTH_TOPICS[:3]])
                ),
            )

    return GuardrailCheckResult(is_supported=True)


def evaluate_retrieval_grounding(
    query: str,
    retrieval_results: List[Dict[str, Any]],
    semantic_threshold: float = 0.40,
) -> GuardrailCheckResult:
    """
    Check if the retrieved chunks provide sufficient evidence to answer the question.
    If no chunks exist or semantic similarity is below threshold, flag as unsupported.
    """
    if not retrieval_results:
        return GuardrailCheckResult(
            is_supported=False,
            reason="NO_EVIDENCE_FOUND",
            suggested_response=(
                f"I searched Lenny's podcast transcripts for **'{query}'**, but could not find sufficient evidence or "
                "direct discussions from guests on this specific topic.\n\n"
                "To ensure strict factual accuracy and avoid hallucination, I only answer using verified quotes and "
                "frameworks from the show.\n\n"
                "You might consider asking about related topics such as:\n"
                + "\n".join([f"- {topic}" for topic in RECOMMENDED_GROWTH_TOPICS[:3]])
            ),
        )

    best_score = max([r.get("semantic_score", 0.0) or 0.0 for r in retrieval_results], default=0.0)
    if best_score < semantic_threshold:
        return GuardrailCheckResult(
            is_supported=False,
            reason="LOW_CONFIDENCE_EVIDENCE",
            suggested_response=(
                f"The available transcript records have low relevance to **'{query}'** (highest match confidence: {best_score:.2f}).\n\n"
                "Rather than providing an ungrounded or speculative answer, I recommend refining the query or exploring "
                "these popular themes from the archive:\n"
                + "\n".join([f"- {topic}" for topic in RECOMMENDED_GROWTH_TOPICS[:3]])
            ),
        )

    return GuardrailCheckResult(is_supported=True)
