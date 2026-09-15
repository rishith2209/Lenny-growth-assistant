from typing import Any, Dict
from sqlalchemy import text
from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.providers.ollama import OllamaProvider
from apps.api.src.providers.anthropic import AnthropicProvider
from apps.api.src.core.config import settings


class HealthService:
    def __init__(self):
        self.ollama = OllamaProvider()
        self.anthropic = AnthropicProvider()

    async def check_database(self) -> Dict[str, Any]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1;"))
                row = result.scalar()
                vec_result = await session.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                )
                has_vector = vec_result.scalar() is not None
                return {
                    "status": "healthy" if row == 1 and has_vector else "degraded",
                    "connected": row == 1,
                    "pgvector_installed": has_vector,
                }
        except Exception as e:
            return {
                "status": "unavailable",
                "connected": False,
                "pgvector_installed": False,
                "error": str(e),
            }

    async def check_providers(self) -> Dict[str, Any]:
        ollama_health = await self.ollama.check_health()
        anthropic_health = await self.anthropic.check_health()

        return {
            "primary_provider": "ollama",
            "providers": {
                "ollama": ollama_health.model_dump(),
                "anthropic": anthropic_health.model_dump(),
            },
        }

    async def get_system_health(self) -> Dict[str, Any]:
        db = await self.check_database()
        provs = await self.check_providers()

        ollama_status = provs["providers"]["ollama"]["status"]

        if db["status"] == "healthy" and ollama_status == "healthy":
            overall = "healthy"
        elif db["status"] == "unavailable" or ollama_status == "unavailable":
            overall = "degraded"
        else:
            overall = "degraded"

        return {
            "status": overall,
            "environment": settings.ENVIRONMENT,
            "database": db,
            "providers": provs,
            "cost_profile": "100% Free / ₹0 spend",
        }
