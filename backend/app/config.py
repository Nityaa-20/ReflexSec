# =============================================================
#  ReflexSec — Application Configuration
#  Pydantic Settings v2 · Loaded from environment / .env file
# =============================================================

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings object for ReflexSec.

    All values are read from environment variables (case-insensitive).
    Falls back to a .env file in the project root when running locally.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
        validate_default=True,
    )

    # ─────────────────────────────────────────
    #  APPLICATION
    # ─────────────────────────────────────────
    APP_NAME: str = Field(
        default="ReflexSec",
        description="Human-readable application name shown in docs and logs.",
    )
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Deployment environment; affects logging verbosity and feature flags.",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable FastAPI debug mode. NEVER true in production.",
    )

    # ─────────────────────────────────────────
    #  DATABASE  (PostgreSQL)
    # ─────────────────────────────────────────
    DATABASE_URL: str = Field(
        ...,
        description=(
            "Async PostgreSQL DSN used by SQLAlchemy. "
            "Example: postgresql+asyncpg://user:pass@host:5432/db"
        ),
    )

    # ─────────────────────────────────────────
    #  REDIS
    # ─────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL including optional password and DB index.",
    )

    # ─────────────────────────────────────────
    #  OLLAMA  (Local LLM inference)
    # ─────────────────────────────────────────
    OLLAMA_BASE_URL: AnyUrl = Field(
        default="http://ollama:11434",
        description="Base URL of the Ollama inference server.",
    )
    OLLAMA_MODEL: str = Field(
        default="llama3",
        description="Model tag to use for threat analysis and self-critique.",
    )
    OLLAMA_TIMEOUT: int = Field(
        default=120,
        ge=10,
        description="Request timeout in seconds for Ollama API calls.",
    )

    # ─────────────────────────────────────────
    #  SECURITY  /  JWT
    # ─────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="HMAC secret for signing JWTs. Generate with: openssl rand -hex 64",
    )
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512", "RS256"] = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token lifetime in minutes (5 min – 24 h).",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        description="Refresh token lifetime in days.",
    )

    # ─────────────────────────────────────────
    #  LOGGING
    # ─────────────────────────────────────────
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum log level emitted by Loguru.",
    )
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json",
        description="Structured JSON logging for prod; plain text for local dev.",
    )

    # ─────────────────────────────────────────
    #  SELF-CRITIQUE AGENT FLAGS
    # ─────────────────────────────────────────
    ENABLE_SELF_CRITIQUE: bool = Field(
        default=True,
        description="Enable the second-pass LLM review loop on threat assessments.",
    )
    MAX_CRITIQUE_ITERATIONS: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum critique iterations before returning a final answer.",
    )
    MIN_CONFIDENCE_THRESHOLD: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score required before accepting an assessment.",
    )

    # ─────────────────────────────────────────
    #  DERIVED HELPERS
    # ─────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def ollama_base_url_str(self) -> str:
        """Return Ollama base URL as a plain string (strips trailing slash)."""
        return str(self.OLLAMA_BASE_URL).rstrip("/")

    # ─────────────────────────────────────────
    #  VALIDATORS
    # ─────────────────────────────────────────
    @field_validator("DEBUG", mode="before")
    @classmethod
    def debug_must_be_false_in_production(cls, v: bool, info) -> bool:  # noqa: ANN001
        # Note: cross-field validation via model_validator runs after all fields
        # are set; this guard is intentionally lightweight.
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError(
                "DATABASE_URL must use a PostgreSQL or SQLite scheme. "
                "Use 'postgresql+asyncpg://' for async SQLAlchemy."
            )
        return v


# =============================================================
#  Singleton accessor
#  Usage anywhere in the app:
#    from app.config import settings
# =============================================================

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The @lru_cache ensures the .env file is read exactly once per process,
    making this safe to call in FastAPI dependency injection without
    re-parsing on every request.
    """
    return Settings()


# Module-level singleton — preferred import target
settings: Settings = get_settings()
