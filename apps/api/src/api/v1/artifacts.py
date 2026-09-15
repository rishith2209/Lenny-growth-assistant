from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.src.db.session import get_db
from apps.api.src.db.models import Artifact, Session
from apps.api.src.schemas.artifact import ArtifactCreate, ArtifactResponse, ArtifactListResponse
from apps.api.src.services.skills.ship30 import (
    count_words,
    validate_ship30_essay,
    generate_atomic_essay_html,
)

router = APIRouter(prefix="/api/v1/artifacts", tags=["Artifacts & Isolated Viewer"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED, summary="Save a generated artifact")
async def create_artifact(
    payload: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify session exists
    session = await db.get(Session, payload.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {payload.session_id} not found")

    actual_words = payload.word_count or count_words(payload.content)
    guest = payload.metadata.get("guest")
    episode_title = payload.metadata.get("episode_title")

    # If essay, pre-render self-contained sandboxed HTML
    rendered = payload.rendered_html
    if not rendered:
        rendered = generate_atomic_essay_html(
            title=payload.title,
            markdown_content=payload.content,
            guest=guest,
            episode_title=episode_title,
            word_count=actual_words,
        )

    # Attach validation metrics to metadata
    validation = validate_ship30_essay(payload.content)
    enhanced_metadata = {
        **payload.metadata,
        "validation": {
            "is_valid": validation.is_valid,
            "has_hook": validation.has_hook,
            "has_core_idea": validation.has_core_idea,
            "has_subheadings": validation.has_subheadings,
            "citation_count": validation.citation_count,
            "warnings": validation.warnings,
        },
    }

    artifact = Artifact(
        session_id=payload.session_id,
        message_id=payload.message_id,
        artifact_type=payload.artifact_type,
        title=payload.title,
        content=payload.content,
        rendered_html=rendered,
        metadata_=enhanced_metadata,
        word_count=actual_words,
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        message_id=artifact.message_id,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        content=artifact.content,
        rendered_html=artifact.rendered_html,
        metadata=artifact.metadata_,
        word_count=artifact.word_count,
        created_at=artifact.created_at,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse, summary="Get artifact details by ID")
async def get_artifact(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
):
    artifact = await db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact {artifact_id} not found")

    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        message_id=artifact.message_id,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        content=artifact.content,
        rendered_html=artifact.rendered_html,
        metadata=artifact.metadata_,
        word_count=artifact.word_count,
        created_at=artifact.created_at,
    )


@router.get("/{artifact_id}/raw", response_class=HTMLResponse, summary="Serve raw sandboxed HTML for secure isolated viewer")
async def get_artifact_raw(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Serves the artifact HTML with strict Content-Security-Policy and isolation headers.
    Combined with iframe sandbox attribute (sandbox='allow-scripts' without 'allow-same-origin'),
    this guarantees zero parent DOM access, zero cookie/storage access, and zero parent API calls.
    """
    artifact = await db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact {artifact_id} not found")

    html_content = artifact.rendered_html or f"<html><body><pre>{artifact.content}</pre></body></html>"

    headers = {
        "Content-Type": "text/html; charset=utf-8",
        # Strict CSP blocking unauthorized scripts, external connections, object/embeds, and forms
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; font-src https: data:; img-src data: https:; base-uri 'none'; form-action 'none';",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "Referrer-Policy": "no-referrer",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cross-Origin-Opener-Policy": "same-origin",
    }

    return HTMLResponse(content=html_content, status_code=200, headers=headers)


@router.get("/session/{session_id}", response_model=ArtifactListResponse, summary="List all artifacts in a session")
async def list_session_artifacts(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Artifact).where(Artifact.session_id == session_id).order_by(Artifact.created_at.desc())
    res = await db.execute(stmt)
    artifacts = res.scalars().all()

    items = [
        ArtifactResponse(
            id=a.id,
            session_id=a.session_id,
            message_id=a.message_id,
            artifact_type=a.artifact_type,
            title=a.title,
            content=a.content,
            rendered_html=a.rendered_html,
            metadata=a.metadata_,
            word_count=a.word_count,
            created_at=a.created_at,
        )
        for a in artifacts
    ]

    return ArtifactListResponse(
        session_id=session_id,
        total=len(items),
        artifacts=items,
    )
