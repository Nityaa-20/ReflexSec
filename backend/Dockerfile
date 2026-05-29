# =============================================================
#  ReflexSec — Backend Dockerfile
#  Python 3.13 · FastAPI · Uvicorn
#  Multi-stage build: builder → runtime
# =============================================================

# ─────────────────────────────────────────
#  STAGE 1 — dependency builder
#  Compiles wheels in an isolated layer so
#  the final image ships no build toolchain.
# ─────────────────────────────────────────
FROM python:3.13-slim AS builder

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# Install OS-level build deps needed to compile native extensions
# (psycopg2-binary bundles libpq, but bcrypt / cryptography need gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip + install wheel builder
RUN pip install --upgrade pip setuptools wheel

# Copy only the dependency manifest first — maximises layer cache hits
COPY requirements.txt .

# Compile all packages into reusable wheels
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ─────────────────────────────────────────
#  STAGE 2 — lean runtime image
# ─────────────────────────────────────────
FROM python:3.13-slim AS runtime

# ── Runtime environment ──────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_HOME=/app \
    PORT=8000

# ── Create non-root user for security ────
RUN groupadd --gid 1001 reflexsec \
    && useradd --uid 1001 --gid reflexsec --shell /bin/bash --create-home reflexsec

# ── Minimal runtime OS packages ──────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# ── Install pre-built wheels (no compiler needed) ──
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# ── Copy application source ──────────────
COPY --chown=reflexsec:reflexsec . .

# ── Create runtime directories ────────────
RUN mkdir -p ${APP_HOME}/logs \
    && chown -R reflexsec:reflexsec ${APP_HOME}

# ── Drop privileges ───────────────────────
USER reflexsec

# ── Expose FastAPI port ───────────────────
EXPOSE ${PORT}

# ── Healthcheck (mirrors docker-compose probe) ──
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ── Use tini as PID 1 for proper signal handling ──
ENTRYPOINT ["/usr/bin/tini", "--"]

# ── Start Uvicorn ─────────────────────────
# Workers are intentionally set to 1 here; scale horizontally via
# Docker Compose replicas or a process manager like Gunicorn in prod.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--log-level", "info", \
     "--access-log"]
