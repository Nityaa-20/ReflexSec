import json
import re
from typing import Any
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from app.services.ollama_service import OllamaService, ollama_service
from app.services.threat_analysis_service import ThreatAnalysisResult
from app.services.cve_agent import CVEAnalysisResult
from app.services.ioc_agent import IOCAnalysisResult
from app.services.self_critique_service import CritiqueResult


# ── Response Schema ──────────────────────────────────────────────────────────

class ReportResult(BaseModel):
    executive_summary: str = Field(..., min_length=1, description="High-level overview of the threat intelligence findings")
    threat_assessment: str = Field(..., min_length=1, description="Detailed threat type, attack methods, and impact assessment")
    risk_analysis: str = Field(..., min_length=1, description="Severity justification, business impact, and exploitability analysis")
    mitigation_strategy: str = Field(..., min_length=1, description="Immediate, short-term, and long-term mitigation actions")
    confidence_assessment: str = Field(..., min_length=1, description="Confidence score explanation incorporating critique findings")
    soc_recommendations: list[str] = Field(..., description="Prioritized, actionable SOC recommendations")

    @field_validator("executive_summary", "threat_assessment", "risk_analysis", "mitigation_strategy", "confidence_assessment")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Report section must be a non-empty string")
        return v.strip()

    @field_validator("soc_recommendations", mode="before")
    @classmethod
    def coerce_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        if not isinstance(v, list):
            raise ValueError("soc_recommendations must be a list of strings")
        coerced = [str(item) for item in v]
        if not coerced:
            raise ValueError("soc_recommendations must contain at least one item")
        return coerced


# ── Section Builders ─────────────────────────────────────────────────────────

def _build_threat_section(r: ThreatAnalysisResult) -> str:
    mitigations = "\n".join(f"    - {m}" for m in r.mitigation)
    return f"""[THREAT ANALYSIS]
  Threat Type    : {r.threat_type}
  Severity       : {r.severity}
  Attack Vector  : {r.attack_vector}
  Mitigations    :
{mitigations}
  Confidence     : {r.confidence_score}"""


def _build_cve_section(r: CVEAnalysisResult) -> str:
    systems = "\n".join(f"    - {s}" for s in r.affected_systems)
    mitigations = "\n".join(f"    - {m}" for m in r.mitigation)
    return f"""[CVE ANALYSIS]
  CVE ID              : {r.cve_id}
  Severity            : {r.severity}
  Exploitability      : {r.exploitability}
  Affected Systems    :
{systems}
  Mitigations         :
{mitigations}
  Confidence          : {r.confidence_score}"""


def _build_ioc_section(r: IOCAnalysisResult) -> str:
    risks = "\n".join(f"    - {risk}" for risk in r.associated_risks)
    actions = "\n".join(f"    - {a}" for a in r.recommended_actions)
    return f"""[IOC INVESTIGATION]
  IOC Value           : {r.ioc_value}
  IOC Type            : {r.ioc_type}
  Threat Level        : {r.threat_level}
  Reputation          : {r.reputation}
  Associated Risks    :
{risks}
  Recommended Actions :
{actions}
  Reasoning           : {r.reasoning}
  Confidence          : {r.confidence_score}"""


def _build_critique_section(r: CritiqueResult) -> str:
    weaknesses = "\n".join(f"    - {w}" for w in r.weaknesses)
    improvements = "\n".join(f"    - {i}" for i in r.improvements)
    return f"""[SELF-CRITIQUE REVIEW]
  Weaknesses          :
{weaknesses}
  Improvements        :
{improvements}
  Revised Confidence  : {r.revised_confidence_score}
  Critique Summary    : {r.critique_summary}"""


# ── Prompt Template ──────────────────────────────────────────────────────────

_REPORT_PROMPT = """You are a senior cyber threat intelligence analyst authoring a professional threat intelligence report for a Security Operations Center (SOC).
Synthesize the agent findings below into a complete, professional report.
Respond ONLY with a valid JSON object — no markdown, no code fences, no preamble, no commentary.

=== INTELLIGENCE FINDINGS ===
{agent_sections}

=== REPORT REQUIREMENTS ===
Produce a professional cyber threat intelligence report with these exact sections:

1. executive_summary
   - High-level overview accessible to non-technical stakeholders
   - Summarise the threat, its significance, and the overall risk posture
   - 2-4 sentences

2. threat_assessment
   - Identified threat type and classification
   - Detailed attack methods and techniques (MITRE ATT&CK references if applicable)
   - Potential impact on systems, data, and operations

3. risk_analysis
   - Severity level with justification based on exploitability and impact
   - Business impact assessment (financial, operational, reputational)
   - Exploitability context (active exploitation, PoC availability, or theoretical)

4. mitigation_strategy
   - Immediate actions (0-24 hours): containment and emergency response
   - Short-term actions (1-30 days): patching, hardening, and monitoring
   - Long-term actions (30+ days): architectural improvements and resilience measures

5. confidence_assessment
   - Explanation of the overall confidence level in the analysis
   - Reference specific critique findings that affected confidence
   - Note any data gaps or limitations that should be considered

6. soc_recommendations
   - Prioritized list of concrete, actionable SOC tasks
   - Each item should be specific enough to assign to an analyst
   - Order by urgency and impact

IMPORTANT:
soc_recommendations MUST be a JSON array of strings.

Correct example:

"soc_recommendations": [
  "Monitor DNS queries for malicious-example.com",
  "Enable PowerShell logging and alerting",
  "Block malicious domains at the firewall"
]

Do NOT create objects inside soc_recommendations.
Do NOT use key-value pairs.
Do NOT use nested JSON structures.

IMPORTANT:

risk_analysis MUST be a single string.

mitigation_strategy MUST be a single string.

confidence_assessment MUST be a single string.

Do NOT return JSON objects for these fields.
Do NOT return nested JSON.
Do NOT return key-value structures.

Correct examples:

"risk_analysis": "High severity due to active exploitation and significant business impact."

"mitigation_strategy": "Immediately isolate affected hosts, patch vulnerable systems, enable enhanced monitoring, and implement long-term security hardening."

"confidence_assessment": "High confidence based on multiple corroborating indicators and consistent threat intelligence findings."

IMPORTANT:
Return ONLY valid JSON.
Do NOT include explanations before the JSON.
Do NOT include markdown code blocks.
Do NOT include comments.
Every property name and string value must use double quotes.
The JSON must be parseable by Python json.loads().

Return exactly this JSON structure:
{{
  "executive_summary": "<professional 2-4 sentence high-level summary>",
  "threat_assessment": "<detailed threat type, attack methods, and impact>",
  "risk_analysis": "single string only",
  "mitigation_strategy": "single string only",
  "confidence_assessment": "single string only",
  "soc_recommendations": [
    "<Priority 1: specific actionable SOC task>",
    "<Priority 2: specific actionable SOC task>",
    "<Priority 3: specific actionable SOC task>"
  ]
}}"""


# ── Service ──────────────────────────────────────────────────────────────────

class ReportGenerationService:
    def __init__(self, ollama: OllamaService = ollama_service) -> None:
        self._ollama = ollama

    async def generate_report(
        self,
        threat_analysis: ThreatAnalysisResult | None = None,
        cve_analysis: CVEAnalysisResult | None = None,
        ioc_analysis: IOCAnalysisResult | None = None,
        critique_result: CritiqueResult | None = None,
    ) -> ReportResult:
        if all(v is None for v in (threat_analysis, cve_analysis, ioc_analysis, critique_result)):
            raise ValueError("At least one agent result must be provided for report generation")

        sections: list[str] = []
        active_agents: list[str] = []

        if threat_analysis is not None:
            sections.append(_build_threat_section(threat_analysis))
            active_agents.append("threat")
        if cve_analysis is not None:
            sections.append(_build_cve_section(cve_analysis))
            active_agents.append("cve")
        if ioc_analysis is not None:
            sections.append(_build_ioc_section(ioc_analysis))
            active_agents.append("ioc")
        if critique_result is not None:
            sections.append(_build_critique_section(critique_result))
            active_agents.append("critique")

        logger.info(
            "Report generation started | agents={} section_count={}",
            active_agents,
            len(sections),
        )

        prompt = _REPORT_PROMPT.format(
            agent_sections="\n\n".join(sections),
        )

        logger.info("Final report prompt length={}", len(prompt))

        try:
            raw_response = await self._ollama.generate(prompt)
        except Exception as exc:
            logger.error("Ollama generation failed during report generation | error={}", exc)
            raise RuntimeError(f"LLM generation failed during report generation: {exc}") from exc

        logger.debug(
            "Raw report response received | response_length={}",
            len(raw_response),
        )

        logger.warning(
            "RAW REPORT RESPONSE:\n{}",
            raw_response
        )

        result = self._parse_response(raw_response)

        logger.success(
            "Report generation complete | soc_recommendations={} confidence_assessment_length={}",
            len(result.soc_recommendations),
            len(result.confidence_assessment),
        )

        return result

    # ── Private helpers ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> ReportResult:
        cleaned = raw.strip()

        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error(
                "No JSON object found in report response | raw_snippet={}",
                cleaned[:500],
            )
            raise ValueError("LLM report response contained no valid JSON object")

        json_str = match.group(0)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error(
                "JSON decode error in report response | error={} snippet={}",
                exc,
                json_str[:300],
            )
            raise ValueError(f"Failed to parse report JSON response: {exc}") from exc

        try:
            result = ReportResult(**data)
        except Exception as exc:
            logger.error(
                "Report response schema validation failed | data={} error={}",
                data,
                exc,
            )
            raise ValueError(f"Report response failed schema validation: {exc}") from exc

        return result


report_generation_service = ReportGenerationService()
