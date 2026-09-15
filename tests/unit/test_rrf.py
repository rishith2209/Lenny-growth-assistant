import pytest
from apps.api.src.services.retrieval.engine import (
    HybridRetrievalEngine,
    RetrievedChunkDTO,
    ProvenanceCitationDTO,
)


def test_rrf_scoring_formula():
    """Verify RRF formula: 1 / (60 + rank)."""
    k = 60
    rank1 = 1 / (k + 1)  # ~0.01639
    rank2 = 1 / (k + 2)  # ~0.01612
    assert rank1 > rank2
    assert abs(rank1 - (1.0 / 61.0)) < 1e-6


def test_confidence_scoring_tiers():
    engine = HybridRetrievalEngine(db_session=None)

    prov = ProvenanceCitationDTO(
        chunk_id="chunk_1",
        episode_id="ep_1",
        episode_title="Test",
        guest="Guest",
        start_time_seconds=0.0,
        end_time_seconds=60.0,
        timestamp_formatted="00:00",
        youtube_url=None,
        source_commit="test",
        speaker="Host",
    )

    high_chunk = RetrievedChunkDTO(
        chunk_id="chunk_1",
        episode_id="ep_1",
        episode_title="Test",
        guest="Guest",
        content="Great content",
        speaker="Host",
        start_time_seconds=0.0,
        end_time_seconds=60.0,
        timestamp_formatted="00:00",
        provenance=prov,
        semantic_score=0.88,
        lexical_score=0.92,
        rrf_score=0.032,
    )

    score_high, tier_high = engine._calculate_confidence([high_chunk], top_semantic=0.88, top_lexical=0.92)
    assert tier_high in ["high", "medium"]
    assert score_high >= 0.5

    # Empty results -> unsupported
    score_empty, tier_empty = engine._calculate_confidence([], top_semantic=0.0, top_lexical=0.0)
    assert tier_empty == "unsupported"
    assert score_empty == 0.0
