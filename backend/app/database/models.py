"""
ReflexSec — Self-Critiquing Cyber Threat Intelligence Agent
SQLAlchemy 2.x ORM Models

Enterprise-grade declarative models for threat intelligence data persistence.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class SeverityLevel(str, enum.Enum):
    """Standardised severity classification aligned with CVSS nomenclature."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ThreatStatus(str, enum.Enum):
    """Lifecycle state of a threat record."""

    NEW = "new"
    ANALYSING = "analysing"
    CONFIRMED = "confirmed"
    MITIGATED = "mitigated"
    FALSE_POSITIVE = "false_positive"
    ARCHIVED = "archived"


class IOCType(str, enum.Enum):
    """Indicator-of-Compromise type taxonomy."""

    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"
    EMAIL = "email"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Threat(Base):
    """
    Core threat record capturing a cyber-threat intelligence artefact.

    Each row represents a discrete threat event or campaign that has been
    ingested from an external or internal source and is subject to the
    ReflexSec analysis pipeline.
    """

    __tablename__ = "threats"

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_threats_confidence_score_range",
        ),
        
        Index("ix_threats_severity", "severity"),
        Index("ix_threats_status", "status"),
        Index("ix_threats_cve_id", "cve_id"),
        Index("ix_threats_created_at", "created_at"),
        Index("ix_threats_source", "source"),
        {"comment": "Cyber threat intelligence artefacts ingested by ReflexSec"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Universally unique identifier for the threat record",
    )

    # Core fields
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Human-readable threat title / headline",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full narrative description of the threat",
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severitylevel", create_type=True),
        nullable=False,
        default=SeverityLevel.MEDIUM,
        comment="CVSS-aligned severity classification",
    )
    cve_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="Associated CVE identifier, e.g. CVE-2024-12345",
    )
    source: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Origin feed or platform that surfaced this threat",
    )
    status: Mapped[ThreatStatus] = mapped_column(
        Enum(ThreatStatus, name="threatstatus", create_type=True),
        nullable=False,
        default=ThreatStatus.NEW,
        comment="Current lifecycle state of the threat record",
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Model confidence in the threat assessment; range [0.0, 1.0]",
    )
    raw_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Unprocessed payload as received from the upstream source",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the record was first persisted",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="UTC timestamp of the most recent mutation",
    )

    # Relationships
    reports: Mapped[list[Report]] = relationship(
        "Report",
        back_populates="threat",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Analysis reports produced for this threat",
    )
    iocs: Mapped[list[IOC]] = relationship(
        "IOC",
        back_populates="threat",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Indicators of compromise associated with this threat",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Threat id={self.id} title={self.title!r} severity={self.severity}>"
        )


# ---------------------------------------------------------------------------


class Report(Base):
    """
    Analysis report produced by the ReflexSec self-critiquing agent pipeline.

    A Report captures the full reasoning lifecycle: initial LLM analysis,
    the agent's self-critique pass, and the refined final output — enabling
    full auditability of AI-generated intelligence.
    """

    __tablename__ = "reports"

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_reports_confidence_score_range",
        ),
        Index("ix_reports_threat_id", "threat_id"),
        Index("ix_reports_created_at", "created_at"),
        {"comment": "Self-critiquing agent analysis reports per threat"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Universally unique identifier for the report",
    )

    # Foreign key
    threat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threats.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent threat this report was generated for",
    )

    # Agent pipeline outputs
    initial_analysis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Raw first-pass analysis produced by the primary agent",
    )
    critique: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Self-critique of the initial analysis identifying weaknesses",
    )
    refined_analysis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Revised analysis incorporating the critique feedback",
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Agent's self-assessed confidence in the refined analysis; [0.0, 1.0]",
    )
    recommendations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Structured remediation or mitigation recommendations",
    )

    # Audit timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the report was persisted",
    )

    # Relationships
    threat: Mapped[Threat] = relationship(
        "Threat",
        back_populates="reports",
        lazy="select",
        doc="The threat this report was generated for",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Report id={self.id} threat_id={self.threat_id} "
            f"confidence={self.confidence_score:.2f}>"
        )


# ---------------------------------------------------------------------------


class AgentLog(Base):
    """
    Immutable audit log entry for every agent action within the pipeline.

    Designed for high-volume append-only writes.  No update path exists;
    rows are inserted once and never mutated, preserving a tamper-evident
    execution trail for compliance and debugging purposes.
    """

    __tablename__ = "agent_logs"

    __table_args__ = (
        Index("ix_agent_logs_agent_name", "agent_name"),
        Index("ix_agent_logs_action", "action"),
        Index("ix_agent_logs_created_at", "created_at"),
        Index("ix_agent_logs_success", "success"),
        Index("ix_agent_logs_agent_action", "agent_name", "action"),
        {"comment": "Append-only audit trail of all agent actions"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Universally unique identifier for the log entry",
    )

    # Agent metadata
    agent_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Logical name / identifier of the agent that produced this entry",
    )
    action: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Discrete action or tool invocation name",
    )

    # Payload capture
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Serialised inputs passed to the agent action",
    )
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Serialised outputs returned by the agent action",
    )

    # Performance & outcome
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Wall-clock execution duration in milliseconds",
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the action completed without error",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Structured error detail when success is False",
    )

    # Audit timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the log entry was written",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AgentLog id={self.id} agent={self.agent_name!r} "
            f"action={self.action!r} success={self.success}>"
        )


# ---------------------------------------------------------------------------


class IOC(Base):
    """
    Indicator of Compromise (IOC) extracted from or associated with a threat.

    Stores atomic observables (IPs, domains, hashes, etc.) with enrichment
    metadata such as reputation scores and source attribution to support
    threat-hunting and detection engineering workflows.
    """

    __tablename__ = "iocs"

    __table_args__ = (
        CheckConstraint(
            "reputation_score >= 0.0 AND reputation_score <= 10.0",
            name="ck_iocs_reputation_score_range",
        ),
        
        Index("ix_iocs_threat_id", "threat_id"),
        Index("ix_iocs_ioc_type", "ioc_type"),
        Index("ix_iocs_value", "value"),
        Index("ix_iocs_created_at", "created_at"),
        UniqueConstraint("ioc_type", "value", name="uq_iocs_type_value"),
        {"comment": "Atomic indicators of compromise linked to threat records"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Universally unique identifier for the IOC record",
    )

    # Foreign key
    threat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threats.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent threat this IOC was extracted from",
    )

    # IOC definition
    ioc_type: Mapped[IOCType] = mapped_column(
        Enum(IOCType, name="ioctype", create_type=True),
        nullable=False,
        comment="Observable type classification",
    )
    value: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Raw observable value, e.g. IP address, domain, SHA-256 hash",
    )

    # Enrichment
    reputation_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Threat reputation score from enrichment providers; range [0.0, 10.0]",
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="Feed or enrichment provider that supplied this IOC",
    )

    # Audit timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the IOC was persisted",
    )

    # Relationships
    threat: Mapped[Threat] = relationship(
        "Threat",
        back_populates="iocs",
        lazy="select",
        doc="The threat record this IOC belongs to",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<IOC id={self.id} type={self.ioc_type} value={self.value!r}>"
        )


# ---------------------------------------------------------------------------


class CVERecord(Base):
    """
    Cached CVE (Common Vulnerabilities and Exposures) record sourced from NVD
    or equivalent authoritative feed.

    Provides a local queryable store of CVE metadata to reduce external API
    latency during threat correlation and report generation.
    """

    __tablename__ = "cve_records"

    __table_args__ = (
        CheckConstraint(
            "cvss_score >= 0.0 AND cvss_score <= 10.0",
            name="ck_cve_records_cvss_score_range",
        ),
        
        UniqueConstraint("cve_id", name="uq_cve_records_cve_id"),
        Index("ix_cve_records_cve_id", "cve_id"),
        Index("ix_cve_records_severity", "severity"),
        Index("ix_cve_records_cvss_score", "cvss_score"),
        Index("ix_cve_records_published_date", "published_date"),
        Index("ix_cve_records_exploit_available", "exploit_available"),
        {"comment": "Local cache of CVE records sourced from NVD or equivalent feeds"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Universally unique identifier for the CVE cache record",
    )

    # CVE identity
    cve_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Canonical CVE identifier, e.g. CVE-2024-12345",
    )

    # Scoring
    cvss_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="CVSS base score; range [0.0, 10.0]",
    )
    severity: Mapped[Optional[SeverityLevel]] = mapped_column(
        Enum(SeverityLevel, name="severitylevel", create_type=False),
        nullable=True,
        comment="Qualitative severity derived from CVSS score",
    )

    # Descriptive
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Official NVD or CNA vulnerability description",
    )

    # Lifecycle dates
    published_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC date the CVE was publicly disclosed",
    )
    last_modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC date the CVE record was last updated by the issuing authority",
    )

    # Exploitation status
    exploit_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether a public proof-of-concept or weaponised exploit is known",
    )

    # Structured references
    references: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Array of reference objects (URL, source, tags) from NVD",
    )

    # Audit timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when the record was cached locally",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CVERecord id={self.id} cve_id={self.cve_id!r} "
            f"cvss={self.cvss_score} severity={self.severity}>"
        )
