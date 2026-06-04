import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.services.ollama_service import OllamaService, ollama_service


# ── Response Schema ──────────────────────────────────────────────────────────

class ThreatAnalysisResult(BaseModel):
    threat_type: str = Field(..., description="Classification of the threat (e.g. SQLi, RCE, Phishing)")
    severity: str = Field(..., description="Assessed severity: critical | high | medium | low | info")
    attack_vector: str = Field(..., description="Explanation of how the attack is carried out")
    mitigation: list[str] = Field(..., description="Ordered list of mitigation recommendations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence between 0.0 and 1.0")
    

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"critical", "high", "medium", "low", "info"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"severity must be one of {allowed}, got '{v}'")
        return normalized

    @field_validator("confidence_score", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        try:
            score = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"confidence_score must be a float, got '{v}'")
        return max(0.0, min(1.0, score))


# ── Prompt Template ──────────────────────────────────────────────────────────

_ANALYSIS_PROMPT = """You are an expert cyber threat intelligence analyst.
Analyze the following threat and respond ONLY with a valid JSON object — no markdown, no code fences, no commentary.

Threat Title: {title}
Threat Description: {description}

Return exactly this JSON structure:
{{
  "threat_type": "<short threat classification>",
  "severity": "<one of: critical | high | medium | low | info>",
  "attack_vector": "<clear explanation of how the attack is executed>",
  "mitigation": [
    "<step 1>",
    "<step 2>"
  ],
  "confidence_score": <float between 0.0 and 1.0>
}}"""


# ── Service ──────────────────────────────────────────────────────────────────

class ThreatAnalysisService:
    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self._ollama = ollama

    async def analyze_threat(
        self,
        title: str,
        description: str,
    ) -> ThreatAnalysisResult:
        logger.info(
            "Starting threat analysis | title={} description_length={}",
            title,
            len(description),
        )

        prompt = _ANALYSIS_PROMPT.format(
            title=title.strip(),
            description=description.strip(),
        )

        try:
            raw_response = await self._ollama.generate(prompt)
        except Exception as exc:
            logger.error(
                "Ollama generation failed during threat analysis | title={} error={}",
                title,
                exc,
            )
            raise RuntimeError(f"LLM generation failed: {exc}") from exc

        logger.debug(
            "Raw LLM response received | title={} length={}",
            title,
            len(raw_response),
        )

        parsed = self._parse_response(raw_response, title)

        logger.success(
            "Threat analysis complete | title={} threat_type={} severity={} confidence={}",
            title,
            parsed.threat_type,
            parsed.severity,
            parsed.confidence_score,
        )

        return parsed

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str, title: str) -> ThreatAnalysisResult:
        cleaned = raw.strip()

        # Strip markdown code fences if the model ignored instructions
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        logger.debug(
            "FULL CLEANED RESPONSE:\n{}",
            cleaned,
        )

        if cleaned.startswith("{") and not cleaned.rstrip().endswith("}"):
            logger.warning("Incomplete JSON detected, auto-closing object")
            cleaned = cleaned.rstrip() + "\n}"
        # Extract the first JSON object in the response as a fallback
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in LLM response | title={} raw={}",
                title,
                cleaned[:500],
            )
            raise ValueError("LLM response did not contain a valid JSON object")

        json_str = match.group(0)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error | title={} error={} snippet={}",
                title,
                exc,
                json_str[:300],
            )
            raise ValueError(f"Failed to parse LLM JSON response: {exc}") from exc

        try:
            result = ThreatAnalysisResult(**data)
        except Exception as exc:
            logger.error(
                "Response schema validation failed | title={} data={} error={}",
                title,
                data,
                exc,
            )
            raise ValueError(f"LLM response failed schema validation: {exc}") from exc

        return result


threat_analysis_service = ThreatAnalysisService()
