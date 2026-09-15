import pytest
from apps.api.src.services.ingestion.parser import (
    TranscriptParser,
    parse_timestamp_to_seconds,
    parse_turn_line,
)


def test_parse_timestamp_to_seconds():
    assert parse_timestamp_to_seconds("00:01:30") == 90.0
    assert parse_timestamp_to_seconds("01:30") == 90.0
    assert parse_timestamp_to_seconds("01:00:00") == 3600.0
    assert parse_timestamp_to_seconds("invalid") is None
    assert parse_timestamp_to_seconds("") is None


def test_parse_turn_line_formats():
    # Format 1: Speaker (timestamp): text
    res1 = parse_turn_line("Lenny (00:02:15): Welcome to the podcast.")
    assert res1 is not None
    assert res1[0] == "Lenny"
    assert res1[1] == "00:02:15"
    assert res1[2] == 135.0
    assert res1[3] == "Welcome to the podcast."

    # Format 2: [timestamp] Speaker: text
    res2 = parse_turn_line("[02:15] Elena Verna: Product-led growth is critical.")
    assert res2 is not None
    assert res2[0] == "Elena Verna"
    assert res2[1] == "02:15"
    assert res2[2] == 135.0
    assert res2[3] == "Product-led growth is critical."

    # Format 3: Speaker: text (no timestamp)
    res3 = parse_turn_line("Host: What is retention?")
    assert res3 is not None
    assert res3[0] == "Host"
    assert res3[1] is None
    assert res3[2] is None
    assert res3[3] == "What is retention?"


def test_parse_episode_with_fixtures():
    parser = TranscriptParser()
    raw_md = """
**Host** (00:00:10): Hello and welcome.
**Guest** (00:00:25): Great to be here today.
"""
    meta = {
        "title": "Interview with Growth Expert - Jane Doe",
        "guest": "Jane Doe",
        "duration": "00:45:00",
        "url": "https://youtube.com/watch?v=123",
    }

    ep = parser.parse_episode("ep_01_jane", raw_md, meta)
    assert ep.id == "ep_01_jane"
    assert ep.title == "Interview with Growth Expert - Jane Doe"
    assert ep.guest == "Jane Doe"
    assert ep.duration_seconds == 2700
    assert len(ep.turns) == 2
    assert ep.turns[0].speaker == "Host"
    assert ep.turns[1].speaker == "Guest"


def test_parse_malformed_transcript():
    parser = TranscriptParser()
    malformed_text = "Just some raw text without any formatting."
    ep = parser.parse_episode("ep_malformed", malformed_text, {})
    assert ep.id == "ep_malformed"
    assert len(ep.turns) == 1
    assert ep.turns[0].speaker == "Narrator"
