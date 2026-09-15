from fastapi import APIRouter
from apps.api.src.services.health import HealthService

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])
health_service = HealthService()


@router.get("", summary="System Health Overview")
async def get_health():
    """Returns overall health, database status, and provider availability."""
    return await health_service.get_system_health()


@router.get("/providers", summary="Detailed LLM Provider Status")
async def get_provider_health():
    """Returns detailed status of local Ollama models and optional providers."""
    return await health_service.check_providers()
