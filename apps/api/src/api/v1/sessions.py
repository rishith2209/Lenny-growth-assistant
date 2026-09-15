from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.api.src.db.session import get_db
from apps.api.src.db.models import Session, Message
from apps.api.src.schemas.session import SessionCreate, SessionResponse, MessageCreate, MessageResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["Session & Message Persistence"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Create a new chat session")
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    session = Session(
        title=payload.title,
        user_metadata=payload.user_metadata,
        provider=payload.provider,
        model=payload.model,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        user_metadata=session.user_metadata,
        provider=session.provider,
        model=session.model,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[],
    )


@router.get("/{session_id}", response_model=SessionResponse, summary="Retrieve a session with messages")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Session).options(selectinload(Session.messages)).where(Session.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    return session


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, summary="Append a message to a session")
async def add_message(
    session_id: str,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify session exists
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    message = Message(
        session_id=session_id,
        role=payload.role,
        content=payload.content,
        metadata_=payload.metadata,
        provider=payload.provider or session.provider,
        model=payload.model or session.model,
        latency_ms=payload.latency_ms,
        token_count=payload.token_count,
        cost_inr=payload.cost_inr,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
