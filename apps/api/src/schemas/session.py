from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    role: str = Field(..., description="Role of message author: 'user', 'assistant', 'system', 'tool'")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    token_count: Optional[int] = None
    cost_inr: float = 0.0


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    metadata: Dict[str, Any]
    provider: Optional[str]
    model: Optional[str]
    latency_ms: Optional[int]
    token_count: Optional[int]
    cost_inr: float
    created_at: datetime


class SessionCreate(BaseModel):
    title: Optional[str] = None
    user_metadata: Dict[str, Any] = Field(default_factory=dict)
    provider: str = Field(default="ollama")
    model: str = Field(default="llama3.1:8b")


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    user_metadata: Dict[str, Any]
    provider: str
    model: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)
