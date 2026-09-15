import time
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger
from apps.api.src.providers.base import (
    LLMProvider,
    ChatMessage,
    ToolDefinition,
    ToolCall,
    CompletionResponse,
    ProviderHealth,
)


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.primary_model = primary_model or settings.PRIMARY_MODEL
        self.fallback_model = fallback_model or settings.FALLBACK_MODEL
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def _format_tools(self, tools: Optional[List[ToolDefinition]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    async def _format_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        formatted = []
        for m in messages:
            msg: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments,
                        },
                    }
                    for tc in m.tool_calls
                ]
            formatted.append(msg)
        return formatted

    async def complete(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> CompletionResponse:
        target_model = model or self.primary_model
        payload = {
            "model": target_model,
            "messages": await self._format_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or 350,
            },
        }

        formatted_tools = await self._format_tools(tools)
        if formatted_tools:
            payload["tools"] = formatted_tools

        start_time = time.time()
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404 and target_model != self.fallback_model:
                    logger.warning(f"Model {target_model} not found. Falling back to {self.fallback_model}")
                    payload["model"] = self.fallback_model
                    target_model = self.fallback_model
                    resp = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                else:
                    raise

        latency_ms = int((time.time() - start_time) * 1000)
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content") or ""

        parsed_tool_calls: Optional[List[ToolCall]] = None
        if "tool_calls" in msg and msg["tool_calls"]:
            parsed_tool_calls = []
            for tc in msg["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        pass
                parsed_tool_calls.append(
                    ToolCall(
                        id=tc.get("id", f"call_{int(time.time()*1000)}"),
                        name=func.get("name", ""),
                        arguments=args,
                    )
                )

        usage = data.get("usage", {})
        return CompletionResponse(
            content=content,
            tool_calls=parsed_tool_calls,
            model=target_model,
            provider="ollama",
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=latency_ms,
            cost_inr=0.0,
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        target_model = model or self.primary_model
        payload = {
            "model": target_model,
            "messages": await self._format_messages(messages),
            "stream": True,
            "options": {"temperature": temperature},
        }
        formatted_tools = await self._format_tools(tools)
        if formatted_tools:
            payload["tools"] = formatted_tools

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/v1/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue

    async def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        import asyncio
        target_model = model or self.embedding_model
        if not texts:
            return []

        sem = asyncio.Semaphore(8)

        async def _embed_one(client: httpx.AsyncClient, text: str) -> List[float]:
            async with sem:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": target_model, "prompt": text},
                )
                resp.raise_for_status()
                return resp.json().get("embedding", [])

        async with httpx.AsyncClient(timeout=60.0) as client:
            tasks = [_embed_one(client, t) for t in texts]
            results = await asyncio.gather(*tasks)

        return list(results)

    async def check_health(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return ProviderHealth(
                        provider="ollama",
                        status="unavailable",
                        details={"error": f"HTTP {resp.status_code}"},
                    )
                models_data = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models_data]

                has_primary = any(self.primary_model in name for name in model_names)
                has_embedding = any(self.embedding_model in name for name in model_names)

                if has_primary and has_embedding:
                    status = "healthy"
                elif has_primary or len(model_names) > 0:
                    status = "degraded"
                else:
                    status = "unavailable"

                return ProviderHealth(
                    provider="ollama",
                    status=status,
                    models_available=model_names,
                    embedding_model_available=has_embedding,
                    details={
                        "base_url": self.base_url,
                        "primary_model_found": has_primary,
                        "embedding_model_found": has_embedding,
                    },
                )
        except Exception as e:
            return ProviderHealth(
                provider="ollama",
                status="unavailable",
                details={"error": str(e)},
            )
