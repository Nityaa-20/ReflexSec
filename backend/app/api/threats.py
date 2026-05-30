from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from loguru import logger

from app.database.db import get_db
from app.database.models import Threat

router = APIRouter(
    prefix="/threats",
    tags=["Threat Intelligence"]
)


# ── Pydantic Models ──────────────────────────────────────────────────────────

class ThreatCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Threat title")
    description: str = Field(..., min_length=1, description="Detailed threat description")
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$", description="Severity level")
    cve_id: Optional[str] = Field(None, pattern=r"^CVE-\d{4}-\d{4,7}$", description="CVE identifier")
    source: str = Field(..., min_length=1, max_length=255, description="Threat intelligence source")


class ThreatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: str
    cve_id: Optional[str]
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class DeleteResponse(BaseModel):
    success: bool
    message: str
    threat_id: int


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=ThreatResponse, status_code=201)
async def create_threat(
    payload: ThreatCreate,
    db: AsyncSession = Depends(get_db),
) -> ThreatResponse:
    logger.info(
        "Creating threat | title={} severity={} cve_id={} source={}",
        payload.title, payload.severity, payload.cve_id, payload.source,
    )

    threat = Threat(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        cve_id=payload.cve_id,
        source=payload.source,
    )

    try:
        db.add(threat)
        await db.commit()
        await db.refresh(threat)
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to create threat | error={}", exc)
        raise HTTPException(status_code=500, detail="Failed to persist threat record")

    logger.success("Threat created | id={} title={}", threat.id, threat.title)
    return ThreatResponse.model_validate(threat)


@router.get("", response_model=list[ThreatResponse])
async def list_threats(
    db: AsyncSession = Depends(get_db),
) -> list[ThreatResponse]:
    logger.info("Fetching all threats")

    try:
        result = await db.execute(select(Threat).order_by(Threat.created_at.desc()))
        threats = result.scalars().all()
    except Exception as exc:
        logger.error("Failed to fetch threats | error={}", exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve threats")

    logger.info("Returned {} threat(s)", len(threats))
    return [ThreatResponse.model_validate(t) for t in threats]


@router.get("/{threat_id}", response_model=ThreatResponse)
async def get_threat(
    threat_id: int,
    db: AsyncSession = Depends(get_db),
) -> ThreatResponse:
    logger.info("Fetching threat | id={}", threat_id)

    try:
        result = await db.execute(select(Threat).where(Threat.id == threat_id))
        threat = result.scalar_one_or_none()
    except Exception as exc:
        logger.error("DB error fetching threat | id={} error={}", threat_id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve threat")

    if threat is None:
        logger.warning("Threat not found | id={}", threat_id)
        raise HTTPException(status_code=404, detail=f"Threat {threat_id} not found")

    logger.info("Threat found | id={} title={}", threat.id, threat.title)
    return ThreatResponse.model_validate(threat)


@router.delete("/{threat_id}", response_model=DeleteResponse)
async def delete_threat(
    threat_id: int,
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    logger.info("Deleting threat | id={}", threat_id)

    try:
        result = await db.execute(select(Threat).where(Threat.id == threat_id))
        threat = result.scalar_one_or_none()
    except Exception as exc:
        logger.error("DB error fetching threat for deletion | id={} error={}", threat_id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve threat for deletion")

    if threat is None:
        logger.warning("Threat not found for deletion | id={}", threat_id)
        raise HTTPException(status_code=404, detail=f"Threat {threat_id} not found")

    try:
        await db.delete(threat)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to delete threat | id={} error={}", threat_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete threat")

    logger.success("Threat deleted | id={}", threat_id)
    return DeleteResponse(
        success=True,
        message=f"Threat {threat_id} successfully deleted",
        threat_id=threat_id,
    )
