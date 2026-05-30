# =============================================================
#  ReflexSec — Health Check Endpoints
#  backend/app/api/health.py
#
#  FastAPI · Async · Python 3.13
# =============================================================

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings
from app.database.db import check_database_health

# =============================================================
#  ROUTER
# =============================================================

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

# =============================================================
#  RESPONSE MODELS
# =============================================================


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["ReflexSec"])
    version: str = Field(..., examples=["0.1.0"])


class DatabaseHealthResponse(BaseModel):
    database: str = Field(..., examples=["healthy", "unhealthy"])


class OllamaHealthResponse(BaseModel):
    ollama: str = Field(..., examples=["healthy", "unhealthy"])
    model: str | None = Field(default=None, examples=["llama3"])


class SystemHealthResponse(BaseModel):
    backend: bool
    database: bool
    ollama: bool
    timestamp: str = Field(..., examples=["2024-01-01T00:00:00.000000+00:00"])


# =============================================================
#  HELPERS
# =============================================================

async def _check_ollama_health() -> bool:
    """
    Probe the Ollama inference server by calling ``GET /api/tags``.

    Returns:
        ``True``  — server responded with HTTP 200.
        ``False`` — connection error, timeout, or non-200 response.
    """
    url = f"{settings.ollama_base_url_str}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
        healthy = response.status_code == 200
        if healthy:
            logger.debug("Ollama health check PASSED — {url}", url=url)
        else:
            logger.warning(
                "Ollama health check returned unexpected status {status} — {url}",
                status=response.status_code,
                url=url,
            )
        return healthy
    except httpx.ConnectError as exc:
        logger.error(
            "Ollama health check FAILED (ConnectError): {error}",
            error=str(exc),
        )
        return False
    except httpx.TimeoutException as exc:
        logger.error(
            "Ollama health check FAILED (Timeout): {error}",
            error=str(exc),
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Ollama health check FAILED (unexpected): {error}",
            error=str(exc),
        )
        return False


# =============================================================
#  ENDPOINTS
# =============================================================


@router.get(
    "",
    summary="Service Liveness",
    response_model=HealthResponse,
    response_class=ORJSONResponse,
)
async def health() -> ORJSONResponse:
    """
    Liveness probe — confirms the API process is alive and the
    event loop is responsive.  Does **not** check downstream
    dependencies; use ``GET /health/system`` for a full picture.

    Returns:
        JSON with ``status``, ``service``, and ``version``.
    """
    logger.debug("GET /health — liveness probe.")
    return ORJSONResponse(
        content={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": "0.1.0",
        }
    )


@router.get(
    "/database",
    summary="Database Health",
    response_model=DatabaseHealthResponse,
    response_class=ORJSONResponse,
)
async def health_database() -> ORJSONResponse:
    """
    Readiness probe for PostgreSQL.

    Executes ``SELECT 1`` via the async engine.  Safe to call
    frequently — uses a raw connection that does not interact
    with any active session or transaction.

    Returns:
        ``{"database": "healthy"}`` or ``{"database": "unhealthy"}``
    """
    logger.debug("GET /health/database — checking PostgreSQL.")
    is_healthy = await check_database_health()
    status_str = "healthy" if is_healthy else "unhealthy"

    if is_healthy:
        logger.info("Database health check: {status}.", status=status_str)
    else:
        logger.error("Database health check: {status}.", status=status_str)

    return ORJSONResponse(
        status_code=200 if is_healthy else 503,
        content={"database": status_str},
    )


@router.get(
    "/ollama",
    summary="Ollama Health",
    response_model=OllamaHealthResponse,
    response_class=ORJSONResponse,
)
async def health_ollama() -> ORJSONResponse:
    """
    Readiness probe for the Ollama inference server.

    Issues an HTTP GET to ``<OLLAMA_BASE_URL>/api/tags`` and
    interprets a 200 response as healthy.

    Returns:
        ``{"ollama": "healthy", "model": "<OLLAMA_MODEL>"}``
        or
        ``{"ollama": "unhealthy", "model": null}``
    """
    logger.debug("GET /health/ollama — checking Ollama at {url}.", url=settings.ollama_base_url_str)
    is_healthy = await _check_ollama_health()
    status_str = "healthy" if is_healthy else "unhealthy"

    if is_healthy:
        logger.info("Ollama health check: {status}.", status=status_str)
    else:
        logger.error("Ollama health check: {status}.", status=status_str)

    return ORJSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "ollama": status_str,
            "model": settings.OLLAMA_MODEL if is_healthy else None,
        },
    )


@router.get(
    "/system",
    summary="Full System Health",
    response_model=SystemHealthResponse,
    response_class=ORJSONResponse,
)
async def health_system() -> ORJSONResponse:
    """
    Aggregate readiness probe — checks all downstream dependencies
    concurrently and returns a single consolidated report.

    Components checked:
    * **backend**  — always ``true`` if this endpoint responds.
    * **database** — PostgreSQL reachability via ``SELECT 1``.
    * **ollama**   — Ollama server reachability via ``/api/tags``.

    Returns:
        JSON with per-component boolean flags and an ISO-8601 UTC
        timestamp.  HTTP 200 when all healthy; HTTP 503 otherwise.
    """
    import asyncio

    logger.info("GET /health/system — running full system health check.")

    db_healthy, ollama_healthy = await asyncio.gather(
        check_database_health(),
        _check_ollama_health(),
    )

    all_healthy = db_healthy and ollama_healthy
    timestamp = datetime.now(UTC).isoformat()

    logger.log(
        "SUCCESS" if all_healthy else "WARNING",
        "System health — backend=True, database={db}, ollama={ollama}",
        db=db_healthy,
        ollama=ollama_healthy,
    )

    return ORJSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "backend": True,
            "database": db_healthy,
            "ollama": ollama_healthy,
            "timestamp": timestamp,
        },
    )
