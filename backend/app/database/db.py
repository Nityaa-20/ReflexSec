# =============================================================
#  ReflexSec — Async Database Layer
#  backend/app/database/db.py
#
#  SQLAlchemy 2.x · asyncpg · PostgreSQL · Python 3.13
# =============================================================

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urlparse, urlunparse

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import settings


# =============================================================
#  INTERNAL UTILITIES
# =============================================================

def _sanitise_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.password:
            safe_netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            return urlunparse(parsed._replace(netloc=safe_netloc))
        return url
    except Exception:  # noqa: BLE001
        return "<unparseable DSN>"


def _validate_database_url(url: str | None) -> str:
    if not url:
        raise ValueError(
            "DATABASE_URL is not configured. "
            "Set it in your .env file or as an environment variable."
        )
    if not url.startswith(("postgresql+asyncpg://", "postgresql://", "sqlite+")):
        raise ValueError(
            f"DATABASE_URL scheme is unsupported: {_sanitise_url(url)}. "
            "Use 'postgresql+asyncpg://' for async SQLAlchemy with PostgreSQL."
        )
    return url


# =============================================================
#  CONFIGURATION VALIDATION
# =============================================================

_DATABASE_URL: str = _validate_database_url(settings.DATABASE_URL)

logger.debug("DATABASE_URL validated: {url}", url=_sanitise_url(_DATABASE_URL))


# =============================================================
#  ASYNC ENGINE
# =============================================================

engine: AsyncEngine = create_async_engine(
    url=_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
    echo_pool=False,
    future=True,
    connect_args={
        "server_settings": {
            "application_name": settings.APP_NAME,
            "jit": "off",
        },
        "command_timeout": 60,
    },
)


# =============================================================
#  SESSION FACTORY
# =============================================================

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# =============================================================
#  DECLARATIVE BASE
# =============================================================

class Base(AsyncAttrs, DeclarativeBase):
    def __repr__(self) -> str:  # pragma: no cover
        try:
            cols: dict[str, Any] = {
                col.name: getattr(self, col.name, None)
                for col in self.__table__.columns  # type: ignore[attr-defined]
            }
            pairs = ", ".join(f"{k}={v!r}" for k, v in cols.items())
            return f"<{self.__class__.__name__}({pairs})>"
        except Exception:  # noqa: BLE001
            return f"<{self.__class__.__name__}>"


# =============================================================
#  FASTAPI DEPENDENCY — get_db()
# =============================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("DB session opened.")
            yield session
            await session.commit()
            logger.debug("DB session committed.")
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("DB session rolled back — SQLAlchemyError: {error}", error=str(exc))
            raise
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            logger.error("DB session rolled back — unexpected error: {error}", error=str(exc))
            raise
        finally:
            await session.close()
            logger.debug("DB session closed.")


# =============================================================
#  DATABASE HEALTH CHECK
# =============================================================

async def check_database_health() -> bool:
    try:
        async with engine.connect() as conn:
            conn: AsyncConnection
            await conn.execute(text("SELECT 1"))
        logger.debug("Database health check: PASSED.")
        return True
    except OperationalError as exc:
        logger.error("Database health check FAILED (OperationalError): {error}", error=str(exc))
        return False
    except SQLAlchemyError as exc:
        logger.error("Database health check FAILED (SQLAlchemyError): {error}", error=str(exc))
        return False
    except Exception as exc:  # noqa: BLE001
        logger.critical("Database health check unexpected error: {error}", error=str(exc))
        return False

# Import all ORM models so SQLAlchemy registers them
import app.database.models

# =============================================================
#  DATABASE LIFECYCLE — init / close
# =============================================================

async def init_database(*, create_tables: bool = False) -> None:
    logger.info("Initialising database → {url}", url=_sanitise_url(_DATABASE_URL))
    try:
        async with engine.begin() as conn:
            conn: AsyncConnection
            await conn.execute(text("SELECT 1"))
            if create_tables:
                logger.info("create_tables=True — running Base.metadata.create_all…")
                await conn.run_sync(Base.metadata.create_all)
                logger.success(
                    "ORM tables created for {count} model(s).",
                    count=len(Base.metadata.tables),
                )
        logger.success(
            "Database initialised — pool ready (pool_size={pool_size}, max_overflow={overflow}).",
            pool_size=engine.pool.size(),        # type: ignore[attr-defined]
            overflow=engine.pool._max_overflow,  # type: ignore[attr-defined]
        )
    except OperationalError as exc:
        logger.critical("Cannot reach PostgreSQL during startup: {error}", error=str(exc))
        raise
    except SQLAlchemyError as exc:
        logger.critical("SQLAlchemy error during initialisation: {error}", error=str(exc))
        raise


async def close_database() -> None:
    logger.info("Closing database connection pool…")
    try:
        await engine.dispose(close=True)
        logger.success("Database connection pool disposed cleanly.")
    except Exception as exc:  # noqa: BLE001
        logger.error("Error while disposing database engine: {error}", error=str(exc))