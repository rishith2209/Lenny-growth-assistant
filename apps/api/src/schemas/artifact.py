from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ArtifactCreate(BaseModel):
    session_id: str = Field(..., description="Parent session ID")
    message_id: Optional[str] = Field(None, description="Triggering message ID")
    artifact_type: str = Field(default="essay", description="Type: essay, markdown, html, json")
    title: str = Field(..., min_length=1, description="Artifact title or headline")
    content: str = Field(..., min_length=1, description="Raw artifact content (Markdown or HTML)")
    rendered_html: Optional[str] = Field(None, description="Pre-rendered standalone HTML with embedded styles")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata including citations, guest, timestamps, word count")
    word_count: int = Field(default=0, description="Measured word count")


class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    message_id: Optional[str] = None
    artifact_type: str
    title: str
    content: str
    rendered_html: Optional[str] = None
    metadata: Dict[str, Any]
    word_count: int
    created_at: datetime


class ArtifactListResponse(BaseModel):
    session_id: str
    total: int
    artifacts: List[ArtifactResponse]
