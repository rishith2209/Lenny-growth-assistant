import json
import time
import httpx
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger
from apps.api.src.db.session import get_db, AsyncSessionLocal
from apps.api.src.db.models import Session, Message
from apps.api.src.services.guardrails import check_query_domain

router = APIRouter(prefix="/api/v1/chat", tags=["Conversational Chat & SSE Streaming"])


class ChatStreamRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional existing session ID. If omitted, a new session is created.")
    message: str = Field(..., min_length=1, description="User prompt or question")
    model: Optional[str] = Field(None, description="Target LLM model (e.g. 'llama3.1:8b', 'qwen3:4b', 'qwen3:8b')")
    provider: Optional[str] = Field(None, description="LLM provider runtime (default: 'ollama')")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)


@router.post("/stream", summary="Stream conversational Pi agent response with session replay and durable persistence")
async def chat_stream(
    payload: ChatStreamRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. Resolve or Create Session
    session_id = payload.session_id
    model = payload.model or "llama3.1:8b"
    provider = payload.provider or "ollama"

    if session_id:
        session = await db.get(Session, session_id)
        if not session:
            session = Session(
                id=session_id,
                title=payload.message[:50] + "...",
                model=model,
                provider=provider,
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        else:
            # Update model/provider if switched
            if payload.model and payload.model != session.model:
                session.model = payload.model
            if payload.provider and payload.provider != session.provider:
                session.provider = payload.provider
            await db.commit()
    else:
        session = Session(
            title=payload.message[:50] + "...",
            model=model,
            provider=provider,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = session.id

    # 2. Persist User Message Immediately (Durability Guarantee)
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=payload.message,
        provider=provider,
        model=model,
        metadata_={"status": "completed"},
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 3. Load Session History for Context Replay
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .where(Message.id != user_msg.id)
        .order_by(Message.created_at.asc())
    )
    res = await db.execute(stmt)
    past_messages = res.scalars().all()

    conversation_history = [
        {"role": m.role, "content": m.content, "metadata": m.metadata_}
        for m in past_messages
    ]

    # Check Domain Guardrail for blatant out-of-domain queries
    guardrail = check_query_domain(payload.message)
    if not guardrail.is_supported:
        async def out_of_domain_stream():
            start_t = time.time()
            yield f"data: {json.dumps({'event_id': f'evt_{int(start_t*1000)}_start', 'session_id': session_id, 'type': 'agent_started', 'model': model, 'provider': provider})}\n\n"
            yield f"data: {json.dumps({'event_id': f'evt_{int(start_t*1000)}_delta', 'session_id': session_id, 'type': 'text_delta', 'delta': guardrail.suggested_response})}\n\n"
            
            # Persist assistant response
            async with AsyncSessionLocal() as local_db:
                ast_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=guardrail.suggested_response,
                    provider=provider,
                    model=model,
                    latency_ms=int((time.time() - start_t) * 1000),
                    metadata_={"status": "completed", "guardrail_triggered": True, "reason": guardrail.reason},
                )
                local_db.add(ast_msg)
                await local_db.commit()

            yield f"data: {json.dumps({'event_id': f'evt_{int(time.time()*1000)}_done', 'session_id': session_id, 'type': 'agent_completed', 'latency_ms': int((time.time() - start_t) * 1000), 'cost_inr': 0.0})}\n\n"

        return StreamingResponse(
            out_of_domain_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id,
                "X-Model": model,
                "X-Provider": provider,
            },
        )

    # 4. Stream Pi Bridge Execution
    candidate_urls = [
        "http://172.27.16.1:4001/internal/agent/run",
        f"{settings.PI_BRIDGE_URL}/internal/agent/run",
        "http://127.0.0.1:4001/internal/agent/run",
        "http://localhost:4001/internal/agent/run",
    ]

    async def event_generator():
        accumulated_text = ""
        collected_events = []
        start_time = time.time()
        final_latency = 0

        client = None
        stream_ctx = None
        try:
            # Attempt connection across candidate bridge URLs
            bridge_res = None
            for target_url in candidate_urls:
                try:
                    c = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=15.0, read=600.0, write=30.0))
                    s_ctx = c.stream(
                        "POST",
                        target_url,
                        json={
                            "session_id": session_id,
                            "prompt": payload.message,
                            "conversation_history": conversation_history,
                            "model": model,
                            "provider": provider,
                            "temperature": payload.temperature,
                        },
                    )
                    res = await s_ctx.__aenter__()
                    if res.status_code == 200:
                        bridge_res = res
                        client = c
                        stream_ctx = s_ctx
                        break
                    else:
                        await s_ctx.__aexit__(None, None, None)
                        await c.aclose()
                except Exception:
                    continue

            if not bridge_res or not client or not stream_ctx:
                err_evt = {
                    "event_id": f"evt_{int(time.time()*1000)}_err",
                    "session_id": session_id,
                    "type": "agent_error",
                    "error_code": "BRIDGE_UNAVAILABLE",
                    "message": "Could not connect to Pi Bridge microservice on port 4001.",
                    "recoverable": False,
                }
                yield f"data: {json.dumps(err_evt)}\n\n"
                return

            buffer = ""
            is_completed = False
            async for chunk in bridge_res.aiter_text():
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines.pop() or ""

                for line in lines:
                    trimmed = line.strip()
                    if not trimmed:
                        continue
                    if trimmed.startswith("data: "):
                        yield f"{trimmed}\n\n"
                        raw_json = trimmed[6:]
                        try:
                            evt = json.loads(raw_json)
                            collected_events.append(evt)
                            if evt.get("type") == "text_delta" and evt.get("delta"):
                                accumulated_text += evt["delta"]
                            elif evt.get("type") in ("agent_completed", "agent_error"):
                                final_latency = evt.get("latency_ms", int((time.time() - start_time) * 1000))
                                is_completed = True
                                break
                        except Exception:
                            pass
                if is_completed:
                    break

            # Persist successful assistant turn
            async with AsyncSessionLocal() as local_db:
                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=accumulated_text or "Response completed.",
                    provider=provider,
                    model=model,
                    latency_ms=final_latency or int((time.time() - start_time) * 1000),
                    metadata_={
                        "status": "completed",
                        "events_count": len(collected_events),
                    },
                )
                local_db.add(assistant_msg)
                await local_db.commit()

        except Exception as exc:
            logger.error(f"Error during SSE agent streaming: {exc}", exc_info=True)
            err_evt = {
                "event_id": f"evt_{int(time.time()*1000)}_err",
                "session_id": session_id,
                "type": "agent_error",
                "error_code": "STREAMING_EXCEPTION",
                "message": str(exc),
                "recoverable": False,
            }
            yield f"data: {json.dumps(err_evt)}\n\n"

            # Persist partial / interrupted turn so conversation state is not lost
            async with AsyncSessionLocal() as local_db:
                interrupted_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=accumulated_text or "[Execution interrupted or failed]",
                    provider=provider,
                    model=model,
                    latency_ms=int((time.time() - start_time) * 1000),
                    metadata_={
                        "status": "interrupted",
                        "error": str(exc),
                    },
                )
                local_db.add(interrupted_msg)
                await local_db.commit()
        finally:
            if stream_ctx:
                try:
                    await stream_ctx.__aexit__(None, None, None)
                except Exception:
                    pass
            if client:
                try:
                    await client.aclose()
                except Exception:
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
            "X-Model": model,
            "X-Provider": provider,
        },
    )
