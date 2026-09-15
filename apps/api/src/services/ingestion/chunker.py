import hashlib
from typing import List, Optional
from pydantic import BaseModel
from apps.api.src.services.ingestion.parser import ParsedEpisode, TranscriptTurn


class TranscriptChunkDTO(BaseModel):
    id: str  # {episode_id}_{chunk_index}
    episode_id: str
    chunk_index: int
    speaker: Optional[str]
    start_time_seconds: Optional[float]
    end_time_seconds: Optional[float]
    timestamp_formatted: Optional[str]
    content: str
    content_hash: str
    token_count: int
    metadata: dict


def format_seconds(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def calculate_content_hash(episode_id: str, index: int, content: str) -> str:
    raw = f"{episode_id}:{index}:{content.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SpeakerAwareChunker:
    def __init__(
        self,
        target_chunk_tokens: int = 350,
        max_chunk_tokens: int = 600,
        min_chunk_tokens: int = 100,
        overlap_turns: int = 1,
    ):
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.overlap_turns = overlap_turns

    def _estimate_tokens(self, text: str) -> int:
        """Heuristic ~1.3 tokens per word."""
        return max(1, int(len(text.split()) * 1.3))

    def _split_long_turn(self, turn: TranscriptTurn) -> List[TranscriptTurn]:
        """Split a long turn into sub-turns preserving speaker and timestamp."""
        words = turn.text.split()
        if not words:
            return []
        
        # Max words per sub-turn (~250 words is ~325 tokens, safely below max_chunk_tokens)
        max_words = 250
        if len(words) <= max_words:
            return [turn]

        sub_turns: List[TranscriptTurn] = []
        for i in range(0, len(words), max_words):
            sub_words = words[i : i + max_words]
            sub_text = " ".join(sub_words)
            sub_turns.append(
                TranscriptTurn(
                    speaker=turn.speaker,
                    timestamp_str=turn.timestamp_str,
                    start_seconds=turn.start_seconds,
                    text=sub_text,
                )
            )
        return sub_turns

    def chunk_episode(self, episode: ParsedEpisode) -> List[TranscriptChunkDTO]:
        if not episode.turns:
            return []

        # First normalize turns: split any long turns
        normalized_turns: List[TranscriptTurn] = []
        for turn in episode.turns:
            if not turn.text or not turn.text.strip():
                continue
            normalized_turns.extend(self._split_long_turn(turn))

        if not normalized_turns:
            return []

        chunks: List[TranscriptChunkDTO] = []
        turn_idx = 0
        chunk_idx = 0
        total_turns = len(normalized_turns)

        while turn_idx < total_turns:
            current_turns: List[TranscriptTurn] = []
            current_tokens = 0
            start_idx = turn_idx

            while turn_idx < total_turns:
                turn = normalized_turns[turn_idx]
                turn_tokens = self._estimate_tokens(turn.text)

                if current_turns and (current_tokens + turn_tokens) > self.max_chunk_tokens:
                    break

                current_turns.append(turn)
                current_tokens += turn_tokens
                turn_idx += 1

                if current_tokens >= self.target_chunk_tokens:
                    break

            if not current_turns:
                # Guarantee forward progress
                turn_idx += 1
                continue

            # Format the text with speaker annotations
            formatted_lines = []
            speakers_in_chunk = set()
            start_time = current_turns[0].start_seconds
            end_time = current_turns[-1].start_seconds

            for t in current_turns:
                speakers_in_chunk.add(t.speaker)
                ts_label = f" ({t.timestamp_str})" if t.timestamp_str else ""
                formatted_lines.append(f"{t.speaker}{ts_label}: {t.text}")

            content_text = "\n".join(formatted_lines).strip()
            if not content_text:
                continue

            primary_speaker = current_turns[0].speaker if len(speakers_in_chunk) == 1 else "Multiple"
            ts_formatted = format_seconds(start_time)
            chunk_id = f"{episode.id}_{chunk_idx:04d}"
            chash = calculate_content_hash(episode.id, chunk_idx, content_text)

            chunk_dto = TranscriptChunkDTO(
                id=chunk_id,
                episode_id=episode.id,
                chunk_index=chunk_idx,
                speaker=primary_speaker,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                timestamp_formatted=ts_formatted,
                content=content_text,
                content_hash=chash,
                token_count=current_tokens,
                metadata={
                    "episode_title": episode.title,
                    "guest": episode.guest,
                    "speakers": list(speakers_in_chunk),
                    "start_turn_idx": start_idx,
                    "end_turn_idx": turn_idx - 1,
                },
            )
            chunks.append(chunk_dto)
            chunk_idx += 1

            # Advance with overlap
            if turn_idx < total_turns and self.overlap_turns > 0:
                new_start = max(start_idx + 1, turn_idx - self.overlap_turns)
                turn_idx = new_start

        return chunks
