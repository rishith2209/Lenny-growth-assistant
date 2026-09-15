import pytest
from apps.api.src.services.ingestion.parser import ParsedEpisode, TranscriptTurn
from apps.api.src.services.ingestion.chunker import SpeakerAwareChunker, calculate_content_hash


def test_calculate_content_hash_deterministic():
    h1 = calculate_content_hash("ep_1", 0, "Hello world")
    h2 = calculate_content_hash("ep_1", 0, "Hello world")
    h3 = calculate_content_hash("ep_1", 1, "Hello world")
    assert h1 == h2
    assert h1 != h3


def test_chunk_short_episode():
    chunker = SpeakerAwareChunker(target_chunk_tokens=200, max_chunk_tokens=400)
    turns = [
        TranscriptTurn(speaker="Host", timestamp_str="00:00:10", start_seconds=10.0, text="Introductory remarks."),
        TranscriptTurn(speaker="Guest", timestamp_str="00:00:30", start_seconds=30.0, text="Short reply about retention."),
    ]
    episode = ParsedEpisode(
        id="ep_short",
        slug="ep_short",
        title="Short Ep",
        guest="Guest",
        turns=turns,
    )

    chunks = chunker.chunk_episode(episode)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.episode_id == "ep_short"
    assert c.chunk_index == 0
    assert "Host (00:00:10): Introductory remarks." in c.content
    assert "Guest (00:00:30): Short reply about retention." in c.content
    assert c.start_time_seconds == 10.0
    assert c.end_time_seconds == 30.0
    assert c.timestamp_formatted == "00:10"


def test_chunk_long_episode_splits():
    chunker = SpeakerAwareChunker(target_chunk_tokens=50, max_chunk_tokens=100, overlap_turns=1)
    # Generate 15 turns
    turns = [
        TranscriptTurn(
            speaker=f"Speaker_{i % 2}",
            timestamp_str=f"00:{i:02d}:00",
            start_seconds=float(i * 60),
            text=f"This is an extensive paragraph number {i} discussing SaaS expansion loops, net retention metrics, and churn diagnostics.",
        )
        for i in range(15)
    ]
    episode = ParsedEpisode(
        id="ep_long",
        slug="ep_long",
        title="Long Episode",
        guest="Speaker_1",
        turns=turns,
    )

    chunks = chunker.chunk_episode(episode)
    assert len(chunks) > 1
    # Check index ordering
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx
        assert chunk.episode_id == "ep_long"
        assert chunk.token_count > 0
        assert len(chunk.content_hash) == 64
