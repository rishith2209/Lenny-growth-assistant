# Lenny Growth Assistant — Developer Helper Script (PowerShell)
param (
    [string]$Command = "help"
)

switch ($Command) {
    "db-up" {
        Write-Host "[Docker] Starting PostgreSQL 16 with pgvector..." -ForegroundColor Cyan
        docker compose up -d postgres
    }
    "migrate" {
        Write-Host "[Alembic] Running database migrations..." -ForegroundColor Cyan
        alembic upgrade head
    }
    "ingest-sample" {
        Write-Host "[Ingestion] Ingesting 5 sample podcast episodes..." -ForegroundColor Cyan
        python scripts/ingest.py --limit 5
    }
    "api" {
        Write-Host "[FastAPI] Starting API backend on http://localhost:8000..." -ForegroundColor Cyan
        uvicorn apps.api.src.main:app --reload --port 8000
    }
    "bridge" {
        Write-Host "[Pi Bridge] Starting Pi Agent microservice on http://localhost:4001..." -ForegroundColor Cyan
        npm run pi:start
    }
    "test" {
        Write-Host "[Pytest] Running automated test suite..." -ForegroundColor Cyan
        python -m pytest tests/unit tests/contract -v
    }
    Default {
        Write-Host "Usage: .\scripts\dev.ps1 [db-up | migrate | ingest-sample | api | bridge | test]" -ForegroundColor Yellow
    }
}
