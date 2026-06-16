import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.database.models import Investigation
from app.services.orchestrator import (
    InvestigationRequest,
    InvestigationResult,
    investigation_orchestrator,
)

router = APIRouter(prefix="/investigate", tags=["Investigation"])


@router.post(
    "/",
    response_model=InvestigationResult,
    status_code=status.HTTP_200_OK,
    summary="Run a multi-agent CTI investigation",
    description="Accepts a threat investigation request and returns a self-critiqued intelligence result.",
)
async def run_investigation(
    request: InvestigationRequest,
    db: AsyncSession = Depends(get_db),
) -> InvestigationResult:
    logger.info(
        "Investigation started | title={} cve_id={} ioc_value={}",
        request.title,
        request.cve_id,
        request.ioc_value,
    )

    try:
        result: InvestigationResult = await investigation_orchestrator.investigate(request)

    except ValueError as exc:
        logger.warning("Investigation validation error | detail={}", str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.error("Investigation runtime error | detail={}", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation runtime failure: {exc}",
        ) from exc

    except Exception as exc:
        logger.exception("Investigation unexpected error | detail={}", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during investigation.",
        ) from exc

    # Determine overall severity
    severity = "medium"
    if result.threat_analysis and result.threat_analysis.severity:
        severity = result.threat_analysis.severity
    elif result.cve_analysis and result.cve_analysis.severity:
        severity = result.cve_analysis.severity
    elif result.ioc_analysis and result.ioc_analysis.threat_level:
        severity = result.ioc_analysis.threat_level

    # Determine threat type
    threat_type = "unknown"
    if result.threat_analysis and result.threat_analysis.threat_type:
        threat_type = result.threat_analysis.threat_type
    elif result.ioc_analysis and result.ioc_analysis.ioc_type:
        threat_type = result.ioc_analysis.ioc_type
    elif request.cve_id:
        threat_type = "cve"

    # Determine title
    title = request.title
    if not title:
        if request.cve_id:
            title = f"Vulnerability Investigation: {request.cve_id}"
        elif request.ioc_value:
            title = f"IOC Investigation: {request.ioc_value}"
        else:
            title = "CTI Investigation"

    # Save to database
    try:
        investigation_uuid = uuid.uuid4()
        result.investigation_id = investigation_uuid

        db_investigation = Investigation(
            id=investigation_uuid,
            title=title,
            severity=severity,
            threat_type=threat_type,
            report_json=result.model_dump(mode="json"),
        )
        db.add(db_investigation)
        await db.commit()
        logger.success("Investigation persisted to database | id={}", db_investigation.id)
    except Exception as db_exc:
        await db.rollback()
        logger.error("Failed to persist investigation history | error={}", db_exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist investigation history: {db_exc}",
        ) from db_exc

    logger.info(
        "Investigation completed | title={} has_critique={} has_report={}",
        request.title,
        result.critique is not None,
        result.report is not None,
    )

    return result