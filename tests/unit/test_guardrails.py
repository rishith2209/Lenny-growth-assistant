import pytest
from apps.api.src.services.guardrails import (
    check_query_domain,
    evaluate_retrieval_grounding,
)


def test_guardrail_detects_out_of_domain():
    queries = [
        "How do I bake a sourdough bread with crusty crust?",
        "What is the best way to change oil in a car engine?",
        "Explain quantum physics and string theory",
        "What are the symptoms of acute pneumonia?",
    ]
    for q in queries:
        res = check_query_domain(q)
        assert res.is_supported is False
        assert res.reason == "OUT_OF_DOMAIN"
        assert "Lenny's Podcast" in res.suggested_response
        assert len(res.alternative_topics) > 0


def test_guardrail_permits_in_domain_growth_queries():
    queries = [
        "What does Elena Verna say about B2B growth loops?",
        "How to measure Product-Market Fit according to Casey Winters?",
        "What are the best frameworks for growth team hiring?",
        "How to price SaaS products effectively?",
    ]
    for q in queries:
        res = check_query_domain(q)
        assert res.is_supported is True
        assert res.reason is None


def test_evaluate_retrieval_grounding_empty_results():
    res = evaluate_retrieval_grounding("Some obscure term", [])
    assert res.is_supported is False
    assert res.reason == "NO_EVIDENCE_FOUND"
    assert "could not find sufficient evidence" in res.suggested_response


def test_evaluate_retrieval_grounding_low_confidence():
    mock_results = [{"semantic_score": 0.22, "content": "irrelevant text"}]
    res = evaluate_retrieval_grounding("Obscure growth topic", mock_results, semantic_threshold=0.40)
    assert res.is_supported is False
    assert res.reason == "LOW_CONFIDENCE_EVIDENCE"
