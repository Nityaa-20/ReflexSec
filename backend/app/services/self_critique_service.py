import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.services.ollama_service import OllamaService, ollama_service
from app.services.threat_analysis_service import ThreatAnalysisResult
from app.services.cve_agent import CVEAnalysisResult
from app.services.ioc_agent import IOCAnalysisResult


# ── Response Schema ──────────────────────────────────────────────────────────

class CritiqueResult(BaseModel):
    weaknesses: list[str] = Field(..., description="Identified weaknesses, gaps, or inconsistencies in the analysis")
    improvements: list[str] = Field(..., description="Concrete, actionable improvement suggestions")
    revised_confidence_score: float = Field(..., ge=0.0, le=1.0, description="Revised aggregate confidence score after critique")
    critique_summary: str = Field(..., description="High-level narrative summary of the critique findings")

    @field_validator("revised_confidence_score", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        try:
            score = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"revised_confidence_score must be a float, got '{v}'")
        return max(0.0, min(1.0, score))

    @field_validator("weaknesses", "improvements", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError("Expected a list of strings")
        return [str(item) for item in v]


# ── Prompt Builders ──────────────────────────────────────────────────────────

def _build_threat_section(r: ThreatAnalysisResult) -> str:
    return f"""[THREAT ANALYSIS AGENT OUTPUT]
  Threat Type    : {r.threat_type}
  Severity       : {r.severity}
  Attack Vector  : {r.attack_vector}
  Mitigation     : {chr(10).join(f"    - {m}" for m in r.mitigation)}
  Reasoning      : {r.reasoning}
  Confidence     : {r.confidence_score}"""


def _build_cve_section(r: CVEAnalysisResult) -> str:
    return f"""[CVE ANALYSIS AGENT OUTPUT]
  CVE ID              : {r.cve_id}
  Severity            : {r.severity}
  Exploitability      : {r.exploitability}
  Affected Systems    : {chr(10).join(f"    - {s}" for s in r.affected_systems)}
  Mitigation          : {chr(10).join(f"    - {m}" for m in r.mitigation)}
  Confidence          : {r.confidence_score}"""


def _build_ioc_section(r: IOCAnalysisResult) -> str:
    return f"""[IOC INVESTIGATION AGENT OUTPUT]
  IOC Value           : {r.ioc_value}
  IOC Type            : {r.ioc_type}
  Threat Level        : {r.threat_level}
  Reputation          : {r.reputation}
  Associated Risks    : {chr(10).join(f"    - {risk}" for risk in r.associated_risks)}
  Recommended Actions : {chr(10).join(f"    - {a}" for a in r.recommended_actions)}
  Reasoning           : {r.reasoning}
  Confidence          : {r.confidence_score}"""


_CRITIQUE_PROMPT = """You are a senior red-team analyst and quality assurance reviewer for a cyber threat intelligence platform.
Your role is to critically evaluate the outputs produced by specialized AI agents and identify flaws, gaps, and inconsistencies.

Respond ONLY with a valid JSON object — no markdown, no code fences, no preamble, no commentary.

=== AGENT OUTPUTS TO REVIEW ===
{agent_sections}

=== CRITIQUE CRITERIA ===
Evaluate each available agent output against ALL of the following:

1. MISSING INFORMATION — Are key fields vague, empty, or insufficiently detailed?
2. SEVERITY INCONSISTENCY — Do severity / threat_level ratings conflict across agents or contradict the described impact?
3. WEAK MITIGATIONS — Are mitigations generic, non-actionable, or missing critical remediation steps?
4. CONFIDENCE CALIBRATION — Are confidence scores inflated or deflated relative to the evidence provided?
5. LOGICAL GAPS — Are there contradictions in reasoning, unexplained conclusions, or unsupported claims?
6. COVERAGE GAPS — Are there threat dimensions, affected systems, or attack paths not addressed?
7. CROSS-AGENT CONSISTENCY — Do findings from multiple agents align, and if not, is the discrepancy explained?

Return exactly this JSON structure:
{{
  "weaknesses": [
    "<specific weakness, gap, or inconsistency identified in the agent outputs>",
    "<additional weakness if found>"
  ],
  "improvements": [
    "<concrete, actionable improvement e.g. specify CVE patch version, add network segmentation step>",
    "<additional improvement>"
  ],
  "revised_confidence_score": <float between 0.0 and 1.0 reflecting aggregate analysis quality after critique>,
  "critique_summary": "<2-4 sentence narrative summarising the overall quality, key findings, and most critical improvement needed>"
}}

Scoring guidance for revised_confidence_score:
- 0.9–1.0 : Analysis is comprehensive, consistent, and highly actionable
- 0.7–0.89: Mostly sound with minor gaps or vague sections
- 0.5–0.69: Moderate issues — missing detail, inconsistencies, or weak mitigations
- 0.3–0.49: Significant weaknesses — incomplete analysis or major logical gaps
- 0.0–0.29: Fundamentally flawed — contradictions, missing critical data, or unusable output"""


# ── Service ──────────────────────────────────────────────────────────────────

class SelfCritiqueService:
    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self._ollama = ollama

    async def critique_analysis(
        self,
        threat_analysis: ThreatAnalysisResult | None = None,
        cve_analysis: CVEAnalysisResult | None = None,
        ioc_analysis: IOCAnalysisResult | None = None,
    ) -> CritiqueResult:
        if threat_analysis is None and cve_analysis is None and ioc_analysis is None:
            raise ValueError("At least one agent result must be provided for critique")

        sections: list[str] = []
        if threat_analysis is not None:
            sections.append(_build_threat_section(threat_analysis))
        if cve_analysis is not None:
            sections.append(_build_cve_section(cve_analysis))
        if ioc_analysis is not None:
            sections.append(_build_ioc_section(ioc_analysis))

        agent_count = len(sections)
        logger.info(
            "Self-critique started | agents_provided={} agents={}",
            agent_count,
            [
                name for name, val in [
                    ("threat", threat_analysis),
                    ("cve", cve_analysis),
                    ("ioc", ioc_analysis),
                ]
                if val is not None
            ],
        )

        prompt = _CRITIQUE_PROMPT.format(
            agent_sections="\n\n".join(sections),
        )

        try:
            raw_response = await self._ollama.generate(prompt)
        except Exception as exc:
            logger.error("Ollama generation failed during self-critique | error={}", exc)
            raise RuntimeError(f"LLM generation failed during self-critique: {exc}") from exc

        logger.debug(
            "Raw critique response received | response_length={}",
            len(raw_response),
        )

        result = self._parse_response(raw_response)

        logger.success(
            "Self-critique complete | weaknesses={} improvements={} revised_confidence={}",
            len(result.weaknesses),
            len(result.improvements),
            result.revised_confidence_score,
        )

        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> CritiqueResult:
        cleaned = raw.strip()

        # Strip markdown code fences if model ignored instructions
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        # Extract first JSON object as fallback for verbose models
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in critique response | raw_snippet={}",
                cleaned[:500],
            )
            raise ValueError("LLM critique response contained no valid JSON object")

        json_str = match.group(0)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error in critique response | error={} snippet={}",
                exc,
                json_str[:300],
            )
            raise ValueError(f"Failed to parse critique JSON response: {exc}") from exc

        try:
            result = CritiqueResult(**data)
        except Exception as exc:
            logger.error(
                "Critique response schema validation failed | data={} error={}",
                data,
                exc,
            )
            raise ValueError(f"Critique response failed schema validation: {exc}") from exc

        return result


self_critique_service = SelfCritiqueService()
