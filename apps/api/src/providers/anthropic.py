from typing import Any, AsyncGenerator, Dict, List, Optional
from apps.api.src.core.config import settings
from apps.api.src.providers.base import (
    LLMProvider,
    ChatMessage,
    ToolDefinition,
    CompletionResponse,
    ProviderHealth,
)


class AnthropicProvider(LLMProvider):
    """
    Optional commercial provider boundary for Anthropic Claude.
    Disabled by default for the mandatory ₹0 demo.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> CompletionResponse:
        if not self.api_key:
            raise RuntimeError(
                "Anthropic API key is not configured. The mandatory default demo uses local Ollama at ₹0 cost."
            )
        raise NotImplementedError("Live Anthropic adapter requires valid API credentials and is strictly optional.")

    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise RuntimeError(
                "Anthropic API key is not configured. The mandatory default demo uses local Ollama at ₹0 cost."
            )
        yield "Anthropic streaming adapter boundary."

    async def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        raise NotImplementedError("Anthropic does not provide native vector embedding models; use Ollama or Voyage.")

    async def check_health(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider="anthropic",
                status="unavailable",
                models_available=[],
                embedding_model_available=False,
                details={"reason": "No ANTHROPIC_API_KEY configured (optional provider)"},
            )
        return ProviderHealth(
            provider="anthropic",
            status="healthy",
            models_available=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            embedding_model_available=False,
            details={"configured": True},
        )
