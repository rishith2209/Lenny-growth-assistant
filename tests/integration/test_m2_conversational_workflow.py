import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.db.models import Session, Message, Artifact
from apps.api.src.services.skills.ship30 import validate_ship30_essay, generate_atomic_essay_html


@pytest.mark.asyncio
async def test_m2_conversational_session_replay_and_isolation():
    session_id_1 = f"conv_test_m2_{uuid.uuid4().hex[:8]}"
    session_id_2 = f"conv_test_m2_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        # 1. Create Session 1
        sess1 = Session(id=session_id_1, title="Turn 1: Adam Fishman Growth Teams", model="llama3.1:8b", provider="ollama")
        db.add(sess1)

        # Turn 1: User message & Assistant grounded answer
        msg1_user = Message(
            session_id=session_id_1,
            role="user",
            content="What does Adam Fishman say about growth teams?",
            model="llama3.1:8b",
            metadata_={"status": "completed"},
        )
        msg1_assistant = Message(
            session_id=session_id_1,
            role="assistant",
            content="Adam Fishman states that the goal is not to find a unicorn human being (00:16:06), but to build a balanced portfolio team.",
            model="llama3.1:8b",
            metadata_={"status": "completed", "citations": ["00:16:06"]},
        )
        db.add_all([msg1_user, msg1_assistant])

        # Turn 2: Follow-up question referencing Turn 1
        msg2_user = Message(
            session_id=session_id_1,
            role="user",
            content="What are the four core competencies in his model?",
            model="llama3.1:8b",
            metadata_={"status": "completed"},
        )
        msg2_assistant = Message(
            session_id=session_id_1,
            role="assistant",
            content="The four buckets are growth execution, customer knowledge, growth strategy, and communication & influence (00:22:18).",
            model="llama3.1:8b",
            metadata_={"status": "completed", "citations": ["00:22:18"]},
        )
        db.add_all([msg2_user, msg2_assistant])

        # Turn 3: Ship 30 Essay Artifact Creation
        essay_markdown = (
            "# The Myth of the Unicorn Growth Leader\n\n"
            "## The Core Idea: Build A Portfolio, Not A Hero\n\n"
            "## The Broken Hiring Playbook\n\n"
            "## Pillar 1: Growth Execution [Adam Fishman, 00:16:06]\n\n"
            "## Pillar 2: Growth Strategy (00:22:18)\n\n"
            "## The Golden Takeaway\n"
        )
        art1 = Artifact(
            session_id=session_id_1,
            message_id=msg2_assistant.id,
            artifact_type="essay",
            title="The Myth of the Unicorn Growth Leader",
            content=essay_markdown,
            rendered_html=generate_atomic_essay_html("The Myth of the Unicorn Growth Leader", essay_markdown, guest="Adam Fishman"),
            word_count=1220,
            metadata_={"guest": "Adam Fishman", "citations": ["00:16:06", "00:22:18"]},
        )
        db.add(art1)

        # 2. Create Independent Session 2 (Isolation Verification)
        sess2 = Session(id=session_id_2, title="Turn 1: Elena Verna PMF", model="qwen3:4b", provider="ollama")
        msg_sess2 = Message(
            session_id=session_id_2,
            role="user",
            content="How does Elena Verna define B2B growth loops?",
            model="qwen3:4b",
            metadata_={"status": "completed"},
        )
        db.add_all([sess2, msg_sess2])

        await db.commit()

    # 3. Verify Session 1 History Replay
    async with AsyncSessionLocal() as db:
        stmt = select(Session).options(selectinload(Session.messages), selectinload(Session.artifacts)).where(Session.id == session_id_1)
        res = await db.execute(stmt)
        retrieved_sess1 = res.scalar_one()

        assert len(retrieved_sess1.messages) == 4
        assert retrieved_sess1.messages[0].role == "user"
        assert retrieved_sess1.messages[1].role == "assistant"
        assert "00:16:06" in retrieved_sess1.messages[1].content
        assert retrieved_sess1.messages[2].role == "user"
        assert "four core competencies" in retrieved_sess1.messages[2].content
        assert len(retrieved_sess1.artifacts) == 1
        assert retrieved_sess1.artifacts[0].title == "The Myth of the Unicorn Growth Leader"
        assert "Adam Fishman" in retrieved_sess1.artifacts[0].metadata_["guest"]

        # 4. Verify Session 2 Isolation (No leakage from Session 1)
        stmt2 = select(Session).options(selectinload(Session.messages), selectinload(Session.artifacts)).where(Session.id == session_id_2)
        res2 = await db.execute(stmt2)
        retrieved_sess2 = res2.scalar_one()

        assert len(retrieved_sess2.messages) == 1
        assert len(retrieved_sess2.artifacts) == 0
        assert "Adam Fishman" not in retrieved_sess2.messages[0].content
        assert retrieved_sess2.model == "qwen3:4b"  # Model switching verified

        # Clean up test sessions
        await db.delete(retrieved_sess1)
        await db.delete(retrieved_sess2)
        await db.commit()
