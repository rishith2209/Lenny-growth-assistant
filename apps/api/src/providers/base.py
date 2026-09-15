from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class CompletionResponse(BaseModel):
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    model: str
    provider: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: int
    cost_inr: float = 0.0


class ProviderHealth(BaseModel):
    provider: str
    status: str  # 'healthy', 'degraded', 'unavailable'
    models_available: List[str] = Field(default_factory=list)
    embedding_model_available: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'ollama', 'anthropic')"""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> CompletionResponse:
        """Generate a completion response with optional tool calling support."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream token deltas as an async generator."""
        pass

    @abstractmethod
    async def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """Generate vector embeddings for input texts."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """Perform a live health and model readiness check."""
        pass
