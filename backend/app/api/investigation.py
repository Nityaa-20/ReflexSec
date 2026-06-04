from fastapi import APIRouter, HTTPException, status
from loguru import logger

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
async def run_investigation(request: InvestigationRequest) -> InvestigationResult:
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

    logger.info(
        "Investigation completed | title={} has_critique={} has_report={}",
        request.title,
        result.critique is not None,
        result.report is not None,
    )

    return result