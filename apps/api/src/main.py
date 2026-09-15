import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger, request_id_ctx
from apps.api.src.db.models import Base
from apps.api.src.db.session import async_engine
from apps.api.src.api.v1.health import router as health_router
from apps.api.src.api.v1.knowledge import router as knowledge_router
from apps.api.src.api.v1.sessions import router as sessions_router
from apps.api.src.api.v1.artifacts import router as artifacts_router
from apps.api.src.api.v1.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized on startup
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verification and table creation completed.")
    except Exception as e:
        logger.warning(f"Note on startup table sync: {e}")
    yield


app = FastAPI(
    title="Lenny Growth Assistant API",
    description="Production backend foundation and hybrid RAG knowledge pipeline for Lenny Growth Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_and_logging_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
    token = request_id_ctx.set(req_id)
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = int((time.time() - start_time) * 1000)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-MS"] = str(process_time)

        # Log request summary
        logger.info(
            f"{request.method} {request.url.path} completed with {response.status_code} in {process_time}ms",
            extra={"props": {"method": request.method, "path": request.url.path, "status": response.status_code, "latency_ms": process_time}},
        )
        return response
    except Exception as e:
        process_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path}: {e}",
            exc_info=True,
            extra={"props": {"method": request.method, "path": request.url.path, "latency_ms": process_time}},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected server error occurred. Please refer to request_id for support.",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )
    finally:
        request_id_ctx.reset(token)


# Include API routers
app.include_router(health_router)
app.include_router(knowledge_router)
app.include_router(sessions_router)
app.include_router(artifacts_router)
app.include_router(chat_router)



import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

web_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web", "dist"))
assets_path = os.path.join(web_dist_path, "assets")

if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")


@app.get("/", summary="Root API Index")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists(os.path.join(web_dist_path, "index.html")):
        return FileResponse(os.path.join(web_dist_path, "index.html"))

    return {
        "name": "Lenny Growth Assistant API",
        "version": "1.0.0",
        "status": "online",
        "cost_model": "₹0 Local Open Weights (Ollama + Pi)",
        "docs": "/docs",
    }

