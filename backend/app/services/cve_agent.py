import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.services.ollama_service import OllamaService, ollama_service


# ── Response Schema ──────────────────────────────────────────────────────────

class CVEAnalysisResult(BaseModel):
    cve_id: str = Field(..., description="CVE identifier e.g. CVE-2024-12345")
    severity: str = Field(..., description="Severity level: critical | high | medium | low | info")
    exploitability: str = Field(..., description="Exploitability assessment: active | poc | theoretical | none")
    affected_systems: list[str] = Field(..., description="List of affected systems, platforms, or software")
    mitigation: list[str] = Field(..., description="Ordered list of mitigation and remediation steps")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence between 0.0 and 1.0")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"critical", "high", "medium", "low", "info"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"severity must be one of {allowed}, got '{v}'")
        return normalized

    @field_validator("exploitability")
    @classmethod
    def validate_exploitability(cls, v: str) -> str:
        allowed = {"active", "poc", "theoretical", "none"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"exploitability must be one of {allowed}, got '{v}'")
        return normalized

    @field_validator("confidence_score", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        try:
            score = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"confidence_score must be a float, got '{v}'")
        return max(0.0, min(1.0, score))

    @field_validator("affected_systems", "mitigation", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError("Expected a list of strings")
        return [str(item) for item in v]


# ── Prompt Template ──────────────────────────────────────────────────────────

_CVE_PROMPT = """You are a senior CVE security researcher and vulnerability analyst.
Analyze the following CVE and respond ONLY with a valid JSON object — no markdown, no code fences, no preamble, no commentary.

CVE ID: {cve_id}
CVE Description: {description}

Return exactly this JSON structure:
{{
  "cve_id": "{cve_id}",
  "severity": "<one of: critical | high | medium | low | info>",
  "exploitability": "<one of: active | poc | theoretical | none>",
  "affected_systems": [
    "<affected OS, software, library, or platform>",
    "<additional affected system if applicable>"
  ],
  "mitigation": [
    "<primary remediation step e.g. apply patch, upgrade version>",
    "<secondary mitigation e.g. WAF rule, network segmentation>",
    "<compensating control if patch unavailable>"
  ],
  "confidence_score": <float between 0.0 and 1.0>
}}

Exploitability definitions:
- active: exploit code exists and is being used in the wild
- poc: proof-of-concept exploit exists but no confirmed active exploitation
- theoretical: vulnerability is understood but no public exploit exists
- none: no known exploitation path identified"""


# ── Agent ────────────────────────────────────────────────────────────────────

class CVEAgent:
    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self._ollama = ollama

    async def analyze_cve(
        self,
        cve_id: str,
        description: str,
    ) -> CVEAnalysisResult:
        normalized_cve_id = cve_id.strip().upper()

        logger.info(
            "CVE analysis started | cve_id={} description_length={}",
            normalized_cve_id,
            len(description),
        )

        prompt = _CVE_PROMPT.format(
            cve_id=normalized_cve_id,
            description=description.strip(),
        )

        try:
            raw_response = await self._ollama.generate(prompt)
        except Exception as exc:
            logger.error(
                "Ollama generation failed during CVE analysis | cve_id={} error={}",
                normalized_cve_id,
                exc,
            )
            raise RuntimeError(f"LLM generation failed for {normalized_cve_id}: {exc}") from exc

        logger.debug(
            "Raw LLM response received | cve_id={} response_length={}",
            normalized_cve_id,
            len(raw_response),
        )

        result = self._parse_response(raw_response, normalized_cve_id)

        logger.success(
            "CVE analysis complete | cve_id={} severity={} exploitability={} confidence={}",
            normalized_cve_id,
            result.severity,
            result.exploitability,
            result.confidence_score,
        )

        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str, cve_id: str) -> CVEAnalysisResult:
        cleaned = raw.strip()

        # Strip markdown code fences if model ignored instructions
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        # Extract first JSON object as fallback for verbose models
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in LLM response | cve_id={} raw_snippet={}",
                cve_id,
                cleaned[:500],
            )
            raise ValueError(f"LLM response contained no valid JSON object for {cve_id}")

        json_str = match.group(0)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error | cve_id={} error={} snippet={}",
                cve_id,
                exc,
                json_str[:300],
            )
            raise ValueError(f"Failed to parse LLM JSON for {cve_id}: {exc}") from exc

        # Ensure cve_id is always consistent with the request
        data["cve_id"] = cve_id

        try:
            result = CVEAnalysisResult(**data)
        except Exception as exc:
            logger.error(
                "CVE response schema validation failed | cve_id={} data={} error={}",
                cve_id,
                data,
                exc,
            )
            raise ValueError(f"LLM response failed schema validation for {cve_id}: {exc}") from exc

        return result


cve_agent = CVEAgent()
