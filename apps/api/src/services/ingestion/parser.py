import re
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class TranscriptTurn(BaseModel):
    speaker: str
    timestamp_str: Optional[str] = None
    start_seconds: Optional[float] = None
    text: str


class ParsedEpisode(BaseModel):
    id: str  # Slug
    slug: str
    title: str
    guest: Optional[str] = None
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    publish_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None
    channel: Optional[str] = None
    view_count: Optional[int] = None
    keywords: Optional[List[str]] = None
    raw_metadata: Dict[str, Any] = {}
    turns: List[TranscriptTurn] = []


def parse_timestamp_to_seconds(ts_str: str) -> Optional[float]:
    """Convert HH:MM:SS or MM:SS to seconds."""
    if not ts_str:
        return None
    parts = ts_str.strip("()[] ").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except (ValueError, TypeError):
        return None
    return None


def parse_turn_line(line: str) -> Optional[Tuple[str, Optional[str], Optional[float], str]]:
    """
    Parse a transcript line matching common formats:
    - "Lenny (00:01:23): Welcome to the podcast..."
    - "[01:23] Lenny: Welcome to the podcast..."
    - "Lenny: Welcome to the podcast..."
    - "**Lenny Rachitsky** (02:15): Welcome..."
    """
    line = line.strip()
    if not line:
        return None

    # Pattern 1: Speaker (timestamp): text
    p1 = re.match(r"^[*_]*([A-Za-z0-9\s\.\'-]+?)[*_]*\s*\(([0-9:]+)\)\s*:\s*(.+)$", line)
    if p1:
        speaker = p1.group(1).strip()
        ts = p1.group(2).strip()
        text = p1.group(3).strip()
        return speaker, ts, parse_timestamp_to_seconds(ts), text

    # Pattern 2: [timestamp] Speaker: text
    p2 = re.match(r"^\[([0-9:]+)\]\s*[*_]*([A-Za-z0-9\s\.\'-]+?)[*_]*\s*:\s*(.+)$", line)
    if p2:
        ts = p2.group(1).strip()
        speaker = p2.group(2).strip()
        text = p2.group(3).strip()
        return speaker, ts, parse_timestamp_to_seconds(ts), text

    # Pattern 3: Speaker: text (no timestamp)
    p3 = re.match(r"^[*_]*([A-Za-z0-9\s\.\'-]+?)[*_]*\s*:\s*(.+)$", line)
    if p3:
        speaker = p3.group(1).strip()
        text = p3.group(2).strip()
        # Avoid treating general markdown headers as speakers
        if not speaker.startswith("#") and len(speaker) < 50:
            return speaker, None, None, text

    return None


class TranscriptParser:
    @staticmethod
    def parse_metadata_file(content: str) -> Dict[str, Any]:
        """Parse JSON or YAML-like metadata."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        meta: Dict[str, Any] = {}
        for line in content.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        return meta

    @classmethod
    def parse_episode(
        cls,
        slug: str,
        transcript_text: str,
        metadata_dict: Optional[Dict[str, Any]] = None,
    ) -> ParsedEpisode:
        meta = metadata_dict or {}

        # Extract guest and title heuristics from slug or metadata
        title = meta.get("title") or meta.get("video_title") or slug.replace("-", " ").title()
        guest = meta.get("guest") or meta.get("guest_name")

        if not guest and " - " in title:
            # Common pattern: "Title - Guest Name" or "Guest Name: Title"
            parts = title.split(" - ")
            if len(parts) >= 2:
                guest = parts[-1].strip()

        turns: List[TranscriptTurn] = []
        current_speaker: Optional[str] = None
        current_ts_str: Optional[str] = None
        current_secs: Optional[float] = None
        current_buffer: List[str] = []

        for line in transcript_text.splitlines():
            line_clean = line.strip()
            if not line_clean:
                continue

            parsed = parse_turn_line(line_clean)
            if parsed:
                # Flush previous turn
                if current_speaker and current_buffer:
                    turns.append(
                        TranscriptTurn(
                            speaker=current_speaker,
                            timestamp_str=current_ts_str,
                            start_seconds=current_secs,
                            text=" ".join(current_buffer),
                        )
                    )
                    current_buffer = []

                current_speaker, current_ts_str, current_secs, turn_text = parsed
                current_buffer.append(turn_text)
            else:
                if current_speaker:
                    current_buffer.append(line_clean)
                else:
                    # Generic narrative before first turn
                    current_speaker = "Narrator"
                    current_buffer.append(line_clean)

        if current_speaker and current_buffer:
            turns.append(
                TranscriptTurn(
                    speaker=current_speaker,
                    timestamp_str=current_ts_str,
                    start_seconds=current_secs,
                    text=" ".join(current_buffer),
                )
            )

        duration = meta.get("duration") or meta.get("duration_seconds")
        if isinstance(duration, str) and ":" in duration:
            duration = int(parse_timestamp_to_seconds(duration) or 0)

        return ParsedEpisode(
            id=slug,
            slug=slug,
            title=title,
            guest=guest,
            youtube_url=meta.get("url") or meta.get("youtube_url"),
            video_id=meta.get("id") or meta.get("video_id"),
            publish_date=meta.get("date") or meta.get("publish_date") or meta.get("upload_date"),
            duration_seconds=int(duration) if duration else None,
            description=meta.get("description"),
            channel=meta.get("channel", "Lenny's Podcast"),
            view_count=int(meta["view_count"]) if meta.get("view_count") else None,
            keywords=meta.get("keywords") if isinstance(meta.get("keywords"), list) else None,
            raw_metadata=meta,
            turns=turns,
        )
