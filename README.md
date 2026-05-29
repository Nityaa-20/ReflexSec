<div align="center">

<h1>🛡️ ReflexSec</h1>

<p><strong>Self-Critiquing Cyber Threat Intelligence Agent</strong></p>

<p>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker Ready"></a>
  <img src="https://img.shields.io/badge/AI%20Powered-Claude%20%7C%20GPT--4-8B5CF6?logo=openai&logoColor=white" alt="AI Powered">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen" alt="Status: Active">
</p>

<p><em>Collect. Analyze. Critique. Refine. Repeat.</em></p>

</div>

---

## 📖 Overview

**ReflexSec** is an autonomous, AI-powered cybersecurity intelligence platform that goes beyond standard threat analysis. It not only collects and correlates threat indicators — CVEs, IPs, domains, and malware hashes — but uniquely employs a **self-critiquing review agent** that challenges its own findings, eliminates noise, and refines intelligence into high-confidence, actionable reports.

The platform is built on a multi-agent architecture where a **Collector Agent** gathers raw threat data, an **Analyst Agent** synthesizes it into structured reports, and a **Critic Agent** audits those reports for accuracy, completeness, and bias — iterating until the intelligence meets a quality threshold.

ReflexSec is designed for security researchers, threat intelligence teams, and SOC analysts who need reliable, context-rich intelligence without the overhead of manual triage.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 **Multi-Source Intelligence Collection** | Aggregates threat data from VirusTotal, Shodan, AlienVault OTX, MISP, and public CVE feeds |
| 🧠 **AI-Driven Threat Analysis** | LLM-powered agent contextualizes IOCs, maps to MITRE ATT&CK techniques, and assesses severity |
| 🔁 **Self-Critiquing Review Loop** | A dedicated Critic Agent audits generated reports and triggers re-analysis when confidence is low |
| 📄 **Refined Intelligence Reports** | Produces structured Markdown/JSON/PDF threat reports with confidence scores and analyst notes |
| ⚡ **Asynchronous Pipeline** | Non-blocking agent orchestration using async task queues for high-throughput processing |
| 🔌 **Modular Plugin System** | Easily extend with new threat feeds, LLM backends, or output formats |
| 🖥️ **REST API & Dashboard** | FastAPI backend with a React-based analyst dashboard for report review and management |
| 🐳 **Docker-First Deployment** | Full containerized setup with Docker Compose for rapid local or cloud deployment |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ReflexSec Platform                        │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Data Sources │    │  Agent Layer  │    │   Output Layer   │   │
│  │              │    │              │    │                  │   │
│  │ • VirusTotal │───▶│  Collector   │    │ • JSON Reports   │   │
│  │ • Shodan     │    │    Agent     │    │ • Markdown Docs  │   │
│  │ • OTX        │    │      │       │    │ • PDF Exports    │   │
│  │ • NVD / CVEs │    │      ▼       │───▶│ • REST API       │   │
│  │ • MISP Feeds │    │   Analyst    │    │ • Dashboard UI   │   │
│  └──────────────┘    │    Agent     │    └──────────────────┘   │
│                       │      │       │                           │
│  ┌──────────────┐    │      ▼       │    ┌──────────────────┐   │
│  │  LLM Backend │    │    Critic    │    │  Storage Layer   │   │
│  │              │◀──▶│    Agent     │    │                  │   │
│  │ • Claude API │    │      │       │    │ • PostgreSQL      │   │
│  │ • OpenAI GPT │    │   (Loop if   │    │ • Redis Cache    │   │
│  │ • Local LLM  │    │  low score)  │    │ • S3 / MinIO     │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Core components:**

- **Collector Agent** — Queries threat intelligence APIs and normalizes raw IOC data into a unified schema.
- **Analyst Agent** — Uses LLMs with structured prompting to contextualize threats, identify attack patterns, and generate preliminary reports.
- **Critic Agent** — Reviews analyst output against factual sources, flags unsubstantiated claims, assigns confidence scores, and routes low-confidence reports back for re-analysis.
- **Orchestrator** — Manages the agent lifecycle, task queuing, retry logic, and the self-critique loop.

---

## 🔄 AI Agent Workflow

```
          ┌─────────────────────────────────────────┐
          │           INPUT: IOC / CVE Query         │
          └───────────────────┬─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Collector Agent   │
                   │  (Multi-source API  │
                   │     aggregation)    │
                   └──────────┬──────────┘
                              │ Raw threat data
                              ▼
                   ┌─────────────────────┐
                   │   Analyst Agent     │
                   │  (LLM-based CVE /   │
                   │  IOC contextuali-   │
                   │   zation + MITRE    │
                   │     mapping)        │
                   └──────────┬──────────┘
                              │ Draft report
                              ▼
                   ┌─────────────────────┐
                   │    Critic Agent     │
                   │  (Self-review loop: │
                   │   fact-check,       │
                   │   score, critique)  │
                   └──────────┬──────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
     Score ≥ Threshold               Score < Threshold
               │                             │
               ▼                             ▼
   ┌───────────────────────┐    ┌────────────────────────┐
   │  Finalize & Export    │    │  Re-analyze with critic │
   │  (JSON / MD / PDF)    │    │  feedback injected back │
   └───────────────────────┘    └────────────┬───────────┘
                                             │
                                     (Max 3 iterations)
```

The self-critique loop is the heart of ReflexSec. If the Critic Agent scores a report below the confidence threshold (default: `0.75`), it generates a structured critique — highlighting gaps, hallucinations, or unsupported claims — and re-submits the critique alongside the original data to the Analyst Agent for a second pass. This iterates up to a configurable maximum before producing a final report with explicit confidence caveats.

---

## 🧰 Technology Stack

**Backend**
- Python 3.10+ — Core application runtime
- FastAPI — REST API and async task handling
- LangChain / LlamaIndex — LLM orchestration and agent framework
- Anthropic Claude API / OpenAI GPT-4 — LLM backbone
- Celery + Redis — Async task queue and caching
- SQLAlchemy + PostgreSQL — Persistent report and IOC storage

**Intelligence Sources**
- VirusTotal API — File/IP/URL/domain reputation
- Shodan API — Exposed service and host intelligence
- AlienVault OTX — Community threat feeds
- NVD / CVE API — Vulnerability data
- MISP (optional) — Threat sharing platform integration

**Frontend**
- React 18 + TypeScript — Analyst dashboard
- TailwindCSS — UI styling
- Recharts — Threat trend visualizations

**Infrastructure**
- Docker + Docker Compose — Containerized deployment
- MinIO — Self-hosted object storage for report artifacts
- Nginx — Reverse proxy

---

## 📁 Folder Structure

```
reflexsec/
├── agents/
│   ├── collector.py          # Multi-source threat data collection
│   ├── analyst.py            # LLM-driven threat analysis
│   ├── critic.py             # Self-critique and scoring logic
│   └── orchestrator.py       # Agent lifecycle and loop control
│
├── api/
│   ├── main.py               # FastAPI entrypoint
│   ├── routes/
│   │   ├── reports.py        # Report CRUD endpoints
│   │   ├── ioc.py            # IOC submission and lookup
│   │   └── health.py         # Health and readiness checks
│   └── schemas/              # Pydantic request/response models
│
├── core/
│   ├── config.py             # Environment and settings management
│   ├── llm.py                # LLM provider abstraction layer
│   ├── prompts/              # Agent prompt templates
│   │   ├── analyst.jinja2
│   │   ├── critic.jinja2
│   │   └── collector.jinja2
│   └── scoring.py            # Confidence scoring engine
│
├── integrations/
│   ├── virustotal.py
│   ├── shodan.py
│   ├── otx.py
│   ├── nvd.py
│   └── misp.py
│
├── models/
│   ├── report.py             # Report ORM model
│   ├── ioc.py                # Indicator of Compromise model
│   └── critique.py           # Critique/review record model
│
├── tasks/
│   ├── celery_app.py         # Celery worker configuration
│   └── analysis_tasks.py     # Async analysis task definitions
│
├── frontend/                 # React analyst dashboard
│   ├── src/
│   └── public/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.frontend
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 🚀 Installation Guide

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the dashboard)
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (for containerized setup)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/reflexsec.git
cd reflexsec
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure your API keys and service URLs:

```env
# LLM Provider (choose one)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
LLM_PROVIDER=anthropic          # anthropic | openai | local

# Threat Intelligence Sources
VIRUSTOTAL_API_KEY=your_vt_key
SHODAN_API_KEY=your_shodan_key
OTX_API_KEY=your_otx_key
NVD_API_KEY=your_nvd_key        # optional but recommended

# Database
DATABASE_URL=postgresql://reflexsec:password@localhost:5432/reflexsec

# Cache
REDIS_URL=redis://localhost:6379/0

# Agent Settings
CRITIC_CONFIDENCE_THRESHOLD=0.75
MAX_CRITIQUE_ITERATIONS=3
```

### 3. Install Python Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Initialize the Database

```bash
alembic upgrade head
```

### 5. Start Services

```bash
# Start the FastAPI server
uvicorn api.main:app --reload --port 8000

# Start the Celery worker (separate terminal)
celery -A tasks.celery_app worker --loglevel=info

# Start the frontend dashboard (separate terminal)
cd frontend && npm install && npm run dev
```

The API will be available at `http://localhost:8000` and the dashboard at `http://localhost:5173`.

---

## 🐳 Running with Docker

The recommended way to run ReflexSec is via Docker Compose, which spins up all required services automatically.

### Quick Start

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Build and start all services
docker compose up --build
```

This starts:
- `reflexsec-api` — FastAPI application on port `8000`
- `reflexsec-worker` — Celery background workers
- `reflexsec-frontend` — React dashboard on port `3000`
- `postgres` — Database on port `5432`
- `redis` — Task queue/cache on port `6379`
- `minio` — Object storage on port `9000`
- `nginx` — Reverse proxy on port `80`

### Useful Docker Commands

```bash
# Run in detached mode
docker compose up -d

# View logs for a specific service
docker compose logs -f reflexsec-api

# Stop all services
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v

# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

### Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/health

# Expected response
{"status": "healthy", "agents": "ready", "version": "1.0.0"}
```

---

## 📡 API Usage

### Submit an IOC for Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ip",
    "value": "198.51.100.42",
    "context": "Observed in phishing campaign targeting financial sector"
  }'
```

### Retrieve a Threat Report

```bash
curl http://localhost:8000/api/reports/{report_id}
```

### Sample Report Output

```json
{
  "report_id": "rpt_8f4a2c19",
  "ioc": "198.51.100.42",
  "type": "ip",
  "confidence_score": 0.91,
  "threat_level": "HIGH",
  "mitre_techniques": ["T1566.001", "T1071.001"],
  "summary": "IP associated with known phishing infrastructure...",
  "critique_iterations": 2,
  "sources": ["virustotal", "shodan", "otx"],
  "generated_at": "2025-11-14T10:32:00Z"
}
```

---

## 🔮 Future Enhancements

- [ ] **Automated STIX/TAXII Export** — Native threat sharing protocol support for integration with enterprise SIEM/SOAR platforms
- [ ] **Graph-Based Threat Clustering** — Visualize relationships between IOCs, threat actors, and campaigns using a knowledge graph
- [ ] **Fine-Tuned Critic Model** — Domain-specific fine-tuning of the critic LLM on labeled CTI datasets for higher precision scoring
- [ ] **Real-Time Feed Monitoring** — Continuous ingestion from streaming threat feeds with automatic alerting
- [ ] **CVE Exploit Prediction** — ML model to predict exploitability likelihood based on historical CVE patterns and dark web signals
- [ ] **Multi-Tenant Support** — Organization-level isolation for managed security service provider (MSSP) deployments
- [ ] **Human-in-the-Loop Review** — Analyst annotation and feedback loop to improve future agent outputs over time
- [ ] **Local LLM Support** — Full offline operation via Ollama with quantized Llama / Mistral models

---

## 🔬 Research Contribution

ReflexSec introduces a novel application of **self-critique loops in agentic AI systems** to the cybersecurity intelligence domain. While self-refining LLM architectures (Constitutional AI, Self-RAG, Reflexion) have demonstrated value in general NLP tasks, their application to structured threat intelligence workflows — where factual precision, source attribution, and confidence calibration are critical — remains underexplored.

**Key contributions of this work:**

1. **Critic-in-the-loop CTI pipeline** — A reproducible agent architecture where a dedicated adversarial critic operates on the same knowledge base as the analyst, reducing hallucination rates in threat reports.

2. **Confidence-Gated Iteration** — A scoring mechanism that quantifies report quality across dimensions (source coverage, claim verifiability, MITRE alignment) and gates output release behind a configurable threshold.

3. **Benchmark Dataset** — A curated set of 500+ labeled CVE/IOC scenarios for evaluating CTI agent output quality, released alongside this codebase.

If you use ReflexSec in your research, please cite:

```bibtex
@software{reflexsec2025,
  title  = {ReflexSec: Self-Critiquing Cyber Threat Intelligence Agent},
  author = {Your Name},
  year   = {2025},
  url    = {https://github.com/your-org/reflexsec}
}
```

---

## 🤝 Contributing

Contributions are welcome and appreciated. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please ensure your code passes existing tests (`pytest`) and includes tests for new functionality. Review `CONTRIBUTING.md` for code style guidelines.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

```
MIT License

Copyright (c) 2025 ReflexSec Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

<div align="center">

Built with 🛡️ for the security community.

**[Documentation](docs/)** · **[Report a Bug](issues/new?template=bug_report.md)** · **[Request a Feature](issues/new?template=feature_request.md)**

</div>
