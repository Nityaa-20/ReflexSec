# =============================================================
#  ReflexSec — FastAPI Application Entry Point
#  backend/app/main.py
# =============================================================

import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from loguru import logger

from app.config import settings
from app.api.health import router as health_router
from app.api.threats import router as threats_router
from app.database.db import init_database

# =============================================================
#  LOGGING SETUP
#  Configure Loguru before anything else runs.
# =============================================================

def _configure_logging() -> None:
    """
    Remove Loguru's default handler and replace it with one that
    matches the LOG_FORMAT and LOG_LEVEL from settings.
    """
    logger.remove()  # drop the default stderr sink

    if settings.LOG_FORMAT == "json":
        fmt = (
            '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level":"{level}",'
            '"name":"{name}",'
            '"message":"{message}",'
            '"extra":{extra}}}'
        )
    else:
        fmt = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        )

    logger.add(
        sys.stdout,
        format=fmt,
        level=settings.LOG_LEVEL,
        colorize=(settings.LOG_FORMAT == "text"),
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
        enqueue=True,          # thread-safe async-safe logging
    )

    # Persist logs to a rotating file regardless of environment
    logger.add(
        "logs/reflexsec_{time:YYYY-MM-DD}.log",
        format=fmt,
        level=settings.LOG_LEVEL,
        rotation="00:00",      # new file at midnight
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=False,        # never write locals to disk in prod
        enqueue=True,
    )


_configure_logging()


# =============================================================
#  LIFESPAN  (startup + shutdown events)
# =============================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """
    Manage application lifecycle.
    Code before `yield`  → runs at startup.
    Code after  `yield`  → runs at shutdown.
    """
    # ── STARTUP ──────────────────────────────────────────────
    startup_ts = time.perf_counter()

    logger.info(
        "Starting {app_name} [{env}] — debug={debug}",
        app_name=settings.APP_NAME,
        env=settings.APP_ENV,
        debug=settings.DEBUG,
    )
    logger.info(
        "Ollama model: {model} at {url}",
        model=settings.OLLAMA_MODEL,
        url=settings.ollama_base_url_str,
    )
    logger.info(
        "Self-critique: enabled={enabled}, max_iterations={iters}, "
        "min_confidence={conf}",
        enabled=settings.ENABLE_SELF_CRITIQUE,
        iters=settings.MAX_CRITIQUE_ITERATIONS,
        conf=settings.MIN_CONFIDENCE_THRESHOLD,
    )

    elapsed = (time.perf_counter() - startup_ts) * 1000
    logger.success(
        "{app_name} is ready — startup completed in {elapsed:.1f} ms",
        app_name=settings.APP_NAME,
        elapsed=elapsed,
    )
    await init_database(create_tables=True)

    yield  # ← application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────
    logger.info(
        "{app_name} is shutting down gracefully.",
        app_name=settings.APP_NAME,
    )


# =============================================================
#  FASTAPI APP FACTORY
# =============================================================

def create_application() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.
    Keeping this in a factory function makes it easy to import
    in tests without triggering side effects at module level.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Self-Critiquing Cyber Threat Intelligence Agent — "
            "powered by local LLMs via Ollama."
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        default_response_class=ORJSONResponse,   # faster JSON serialisation
        lifespan=lifespan,
        debug=settings.DEBUG,
    )

    # ── CORS Middleware ───────────────────────────────────────
    # Tighten `allow_origins` in production via an env var;
    # wildcard is acceptable only during local development.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # API Routers
    application.include_router(health_router)
    application.include_router(threats_router)
    return application


app: FastAPI = create_application()


# =============================================================
#  REQUEST LOGGING MIDDLEWARE
# =============================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):  # noqa: ANN001, ANN201
    """Log every inbound request and its response time."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "{method} {path} → {status} ({duration:.1f} ms)",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration_ms,
    )
    return response


# =============================================================
#  ROUTES
# =============================================================

@app.get(
    "/",
    summary="Root",
    tags=["System"],
    status_code=status.HTTP_200_OK,
)
async def root() -> ORJSONResponse:
    """
    Root endpoint — confirms the service is reachable.

    Returns:
        JSON with project name and running status.
    """
    return ORJSONResponse(
        content={
            "project": "ReflexSec",
            "status": "running",
        }
    )



@app.get(
    "/info",
    summary="Application Info",
    tags=["System"],
    status_code=status.HTTP_200_OK,
)
async def info() -> ORJSONResponse:
    """
    Exposes non-sensitive runtime configuration.
    Useful for confirming which model and environment are active.

    Returns:
        JSON with app name, environment, and active Ollama model.
    """
    return ORJSONResponse(
        content={
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "ollama_model": settings.OLLAMA_MODEL,
            "self_critique_enabled": settings.ENABLE_SELF_CRITIQUE,
            "max_critique_iterations": settings.MAX_CRITIQUE_ITERATIONS,
        }
    )
