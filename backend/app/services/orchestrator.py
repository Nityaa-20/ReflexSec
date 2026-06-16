import uuid
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, model_validator


from app.services.threat_analysis_service import (
    ThreatAnalysisService,
    ThreatAnalysisResult,
    threat_analysis_service,
)
from app.services.cve_agent import CVEAgent, CVEAnalysisResult, cve_agent
from app.services.ioc_agent import IOCAgent, IOCAnalysisResult, ioc_agent
from app.services.self_critique_service import (
    SelfCritiqueService,
    CritiqueResult,
    self_critique_service,
)
from app.services.report_generation_service import (
    ReportGenerationService,
    ReportResult,
    report_generation_service,
)


# ── Request / Result Models ──────────────────────────────────────────────────

class InvestigationRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255, description="Threat title for threat analysis")
    description: str | None = Field(None, min_length=1, description="Threat description for threat analysis")
    cve_id: str | None = Field(None, pattern=r"^CVE-\d{4}-\d{4,7}$", description="CVE identifier e.g. CVE-2024-12345")
    cve_description: str | None = Field(None, min_length=1, description="CVE description for CVE analysis")
    ioc_value: str | None = Field(None, min_length=1, description="IOC value: IP, domain, URL, hash, or email")

    @model_validator(mode="after")
    def require_at_least_one_input(self) -> "InvestigationRequest":
        has_threat = self.title is not None and self.description is not None
        has_cve = self.cve_id is not None and self.cve_description is not None
        has_ioc = self.ioc_value is not None

        if not any([has_threat, has_cve, has_ioc]):
            raise ValueError(
                "At least one complete input group is required: "
                "threat (title + description), CVE (cve_id + cve_description), or IOC (ioc_value)"
            )
        return self

    @property
    def has_threat_input(self) -> bool:
        return self.title is not None and self.description is not None

    @property
    def has_cve_input(self) -> bool:
        return self.cve_id is not None and self.cve_description is not None

    @property
    def has_ioc_input(self) -> bool:
        return self.ioc_value is not None


class InvestigationResult(BaseModel):
    investigation_id: uuid.UUID | None = Field(None, description="Database unique identifier of the investigation record")
    threat_analysis: ThreatAnalysisResult | None = Field(None, description="Threat analysis agent output")
    cve_analysis: CVEAnalysisResult | None = Field(None, description="CVE analysis agent output")
    ioc_analysis: IOCAnalysisResult | None = Field(None, description="IOC investigation agent output")
    critique: CritiqueResult | None = Field(None, description="Self-critique agent output")
    report: ReportResult | None = Field(
        None,
        description="Final synthesized threat intelligence report"
    )

# ── Orchestrator ─────────────────────────────────────────────────────────────

class InvestigationOrchestrator:
    def __init__(
        self,
        threat_service: ThreatAnalysisService = threat_analysis_service,
        cve_service: CVEAgent = cve_agent,
        ioc_service: IOCAgent = ioc_agent,
        critique_service: SelfCritiqueService = self_critique_service,
        report_service: ReportGenerationService = report_generation_service,
    ) -> None:
        self._threat_service = threat_service
        self._cve_service = cve_service
        self._ioc_service = ioc_service
        self._critique_service = critique_service
        self._report_service = report_service

    async def investigate(self, request: InvestigationRequest) -> InvestigationResult:
        logger.info(
            "Investigation started | has_threat={} has_cve={} has_ioc={}",
            request.has_threat_input,
            request.has_cve_input,
            request.has_ioc_input,
        )

        threat_result: ThreatAnalysisResult | None = None
        cve_result: CVEAnalysisResult | None = None
        ioc_result: IOCAnalysisResult | None = None
        critique_result: CritiqueResult | None = None

        # ── Step 1: Threat Analysis ──────────────────────────────────────────
        if request.has_threat_input:
            logger.info("Running threat analysis agent | title={}", request.title)
            try:
                threat_result = await self._threat_service.analyze_threat(
                    title=request.title,  # type: ignore[arg-type]
                    description=request.description,  # type: ignore[arg-type]
                )
                logger.success(
                    "Threat analysis complete | severity={} confidence={}",
                    threat_result.severity,
                    threat_result.confidence_score,
                )
            except Exception as exc:
                logger.error("Threat analysis agent failed | title={} error={}", request.title, exc)
                raise RuntimeError(f"Threat analysis failed: {exc}") from exc

        # ── Step 2: CVE Analysis ─────────────────────────────────────────────
        if request.has_cve_input:
            logger.info("Running CVE analysis agent | cve_id={}", request.cve_id)
            try:
                cve_result = await self._cve_service.analyze_cve(
                    cve_id=request.cve_id,  # type: ignore[arg-type]
                    description=request.cve_description,  # type: ignore[arg-type]
                )
                logger.success(
                    "CVE analysis complete | cve_id={} severity={} exploitability={} confidence={}",
                    cve_result.cve_id,
                    cve_result.severity,
                    cve_result.exploitability,
                    cve_result.confidence_score,
                )
            except Exception as exc:
                logger.error("CVE analysis agent failed | cve_id={} error={}", request.cve_id, exc)
                raise RuntimeError(f"CVE analysis failed: {exc}") from exc

        # ── Step 3: IOC Analysis ─────────────────────────────────────────────
        if request.has_ioc_input:
            logger.info("Running IOC investigation agent | ioc_value={}", request.ioc_value)
            try:
                ioc_result = await self._ioc_service.analyze_ioc(
                    ioc_value=request.ioc_value,  # type: ignore[arg-type]
                )
                logger.success(
                    "IOC analysis complete | ioc_type={} threat_level={} reputation={} confidence={}",
                    ioc_result.ioc_type,
                    ioc_result.threat_level,
                    ioc_result.reputation,
                    ioc_result.confidence_score,
                )
            except Exception as exc:
                logger.error("IOC agent failed | ioc_value={} error={}", request.ioc_value, exc)
                raise RuntimeError(f"IOC analysis failed: {exc}") from exc

        # ── Step 4: Self-Critique ────────────────────────────────────────────
        logger.info("Skipping self-critique temporarily")
        critique_result = None

        # ── Step 5: Report Generation ────────────────────────────────────────
        logger.info("Running report generation service")

        report_result = await self._report_service.generate_report(
            threat_analysis=threat_result,
            cve_analysis=cve_result,
            ioc_analysis=ioc_result,
            critique_result=critique_result,
        )

        logger.success(
            "Report generation complete | soc_recommendations={}",
            len(report_result.soc_recommendations),
        )

        # ── Step 6: Assemble Result ──────────────────────────────────────────
        result = InvestigationResult(
            threat_analysis=threat_result,
            cve_analysis=cve_result,
            ioc_analysis=ioc_result,
            critique=critique_result,
            report=report_result,
        )

        logger.success(
            "Investigation complete | agents_ran={} critique={} report=ready",
            sum(1 for x in (threat_result, cve_result, ioc_result) if x is not None),
            critique_result is not None,
        )

        return result


investigation_orchestrator = InvestigationOrchestrator()
