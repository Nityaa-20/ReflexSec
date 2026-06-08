import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.services.ollama_service import OllamaService, ollama_service


# ── IOC Type Detection ───────────────────────────────────────────────────────

_IPV4_RE = re.compile(
    r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)
_IPV6_RE = re.compile(r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^fe80:.*$", re.IGNORECASE)
_DOMAIN_RE = re.compile(r"^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_MD5_RE = re.compile(r"^[a-fA-F0-9]{32}$")
_SHA1_RE = re.compile(r"^[a-fA-F0-9]{40}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_SHA512_RE = re.compile(r"^[a-fA-F0-9]{128}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _detect_ioc_type(value: str) -> str:
    v = value.strip()
    if _URL_RE.match(v):
        return "url"
    if _EMAIL_RE.match(v):
        return "email"
    if _IPV4_RE.match(v) or _IPV6_RE.match(v):
        return "ip_address"
    if _SHA512_RE.match(v):
        return "hash_sha512"
    if _SHA256_RE.match(v):
        return "hash_sha256"
    if _SHA1_RE.match(v):
        return "hash_sha1"
    if _MD5_RE.match(v):
        return "hash_md5"
    if _DOMAIN_RE.match(v):
        return "domain"
    return "unknown"


# ── Response Schema ──────────────────────────────────────────────────────────

class IOCAnalysisResult(BaseModel):
    ioc_value: str = Field(..., description="The original IOC value submitted for analysis")
    ioc_type: str = Field(..., description="Detected IOC type: ip_address | domain | url | hash_md5 | hash_sha1 | hash_sha256 | hash_sha512 | email | unknown")
    threat_level: str = Field(..., description="Threat level: critical | high | medium | low | benign")
    reputation: str = Field(..., description="Reputation: malicious | suspicious | unknown | clean")
    associated_risks: list[str] = Field(..., description="List of malicious activities or threat categories associated with this IOC")
    recommended_actions: list[str] = Field(..., description="Ordered list of defensive and investigative actions")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence between 0.0 and 1.0")
    reasoning: str = Field(..., description="Analyst reasoning behind the assessment")

    @field_validator("threat_level")
    @classmethod
    def validate_threat_level(cls, v: str) -> str:
        allowed = {"critical", "high", "medium", "low", "benign"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"threat_level must be one of {allowed}, got '{v}'")
        return normalized

    @field_validator("reputation")
    @classmethod
    def validate_reputation(cls, v: str) -> str:
        allowed = {"malicious", "suspicious", "unknown", "clean"}
        normalized = v.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"reputation must be one of {allowed}, got '{v}'")
        return normalized

    @field_validator("confidence_score", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        try:
            score = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"confidence_score must be a float, got '{v}'")
        return max(0.0, min(1.0, score))

    @field_validator("associated_risks", "recommended_actions", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError("Expected a list of strings")
        return [str(item) for item in v]


# ── Prompt Template ──────────────────────────────────────────────────────────

_IOC_PROMPT = """You are a senior threat intelligence analyst specializing in Indicator of Compromise (IOC) investigation.
Analyze the following IOC and respond ONLY with a valid JSON object — no markdown, no code fences, no preamble, no commentary.

IOC Value: {ioc_value}
IOC Type: {ioc_type}

Return exactly this JSON structure:
{{
  "ioc_value": "{ioc_value}",
  "ioc_type": "{ioc_type}",
  "threat_level": "<one of: critical | high | medium | low | benign>",
  "reputation": "<one of: malicious | suspicious | unknown | clean>",
  "associated_risks": [
    "<malicious activity or threat category e.g. C2 communication, phishing, malware distribution>",
    "<additional threat category if applicable>"
  ],
  "recommended_actions": [
    "<immediate action e.g. block at firewall, quarantine host>",
    "<investigative action e.g. search SIEM for related activity>",
    "<long-term hardening measure>"
  ],
  "confidence_score": <float between 0.0 and 1.0>,
  "reasoning": "<detailed analyst reasoning covering reputation signals, context, and confidence justification>"
}}

IOC type context:
- ip_address: assess geolocation risk, known threat actor infrastructure, botnet/C2 usage
- domain: assess registration age, DGA patterns, known malicious hosting, typosquatting
- url: assess path patterns, hosting domain, known payload delivery, phishing indicators
- hash_md5 / hash_sha1 / hash_sha256 / hash_sha512: assess known malware families, packer signatures, sandbox behavior
- email: assess spoofing patterns, phishing campaigns, BEC indicators, domain reputation
- unknown: perform best-effort analysis based on the value's structure and content

Threat level definitions:
- critical: actively used in attacks, confirmed malicious with high impact
- high: strong malicious indicators, likely threat actor infrastructure
- medium: suspicious patterns, potentially malicious
- low: minor indicators, unlikely but not ruled out
- benign: no threat indicators, likely legitimate"""


# ── Agent ────────────────────────────────────────────────────────────────────

class IOCAgent:
    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self._ollama = ollama

    async def analyze_ioc(self, ioc_value: str) -> IOCAnalysisResult:
        normalized_value = ioc_value.strip()
        detected_type = _detect_ioc_type(normalized_value)

        logger.info(
            "IOC analysis started | ioc_value={} detected_type={}",
            normalized_value,
            detected_type,
        )

        prompt = _IOC_PROMPT.format(
            ioc_value=normalized_value,
            ioc_type=detected_type,
        )

        try:
            raw_response = await self._ollama.generate(prompt)
        except Exception as exc:
            logger.error(
                "Ollama generation failed during IOC analysis | ioc_value={} error={}",
                normalized_value,
                exc,
            )
            raise RuntimeError(f"LLM generation failed for IOC '{normalized_value}': {exc}") from exc

        logger.debug(
            "Raw LLM response received | ioc_value={} response_length={}",
            normalized_value,
            len(raw_response),
        )

        result = self._parse_response(raw_response, normalized_value, detected_type)

        logger.success(
            "IOC analysis complete | ioc_value={} type={} threat_level={} reputation={} confidence={}",
            normalized_value,
            result.ioc_type,
            result.threat_level,
            result.reputation,
            result.confidence_score,
        )

        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_response(
        self,
        raw: str,
        ioc_value: str,
        detected_type: str,
    ) -> IOCAnalysisResult:
        cleaned = raw.strip()

        # Strip markdown code fences if model ignored instructions
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        if cleaned.startswith("{") and not cleaned.rstrip().endswith("}"):
            logger.warning(
                "Incomplete JSON detected, auto-closing IOC object | ioc_value={}",
                ioc_value,
            )
            cleaned = cleaned.rstrip() + "\n}"
        logger.debug(
            "IOC CLEANED RESPONSE:\n{}",
            cleaned,
        )
        
        # Extract first JSON object as fallback for verbose models
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in LLM response | ioc_value={} raw_snippet={}",
                ioc_value,
                cleaned[:500],
            )
            raise ValueError(f"LLM response contained no valid JSON object for IOC '{ioc_value}'")

        json_str = match.group(0)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error | ioc_value={} error={} snippet={}",
                ioc_value,
                exc,
                json_str[:300],
            )
            raise ValueError(f"Failed to parse LLM JSON for IOC '{ioc_value}': {exc}") from exc

        # Always enforce request values to prevent LLM hallucination
        data["ioc_value"] = ioc_value
        data["ioc_type"] = detected_type

        try:
            result = IOCAnalysisResult(**data)
        except Exception as exc:
            logger.error(
                "IOC response schema validation failed | ioc_value={} data={} error={}",
                ioc_value,
                data,
                exc,
            )
            raise ValueError(
                f"LLM response failed schema validation for IOC '{ioc_value}': {exc}"
            ) from exc

        return result


ioc_agent = IOCAgent()
