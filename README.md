# TMB Tumor Mutation Burden Calc

> **Domain:** Medical Oncology & Cancer Staging Systems
> **Reference Guidelines & Standards:** AJCC Cancer Staging Manual & NCCN Clinical Practice Guidelines

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Tumor Mutational Burden (TMB) Calculator

Calculates somatic mutations per megabase (mut/Mb) from targeted gene panels
or whole-exome sequencing (WES) with FDA-approved thresholds.

References:
  - Marabelle A et al. Lancet Oncol. 2020;21(1):71-82 (KEYNOTE-158 TMB-H)
  - FDA Approval: Pembrolizumab for TMB-H (>=10 mut/Mb) solid tumors (June 2020)
  - Stenzinger A et al. J Immunother Cancer. 2019;7(1):185 (TMB harmonization)
  - Chalmers ZR et al. Genome Med. 2017;9(1):34 (FoundationOne CDx panel)

License: MIT

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/tmb-tumor-mutation-burden-calc.git
cd tmb-tumor-mutation-burden-calc

# Install core (stdlib-only TMB calculation)
pip install -e .

# Install with API server support
pip install -e ".[api]"

# Install with test dependencies
pip install -e ".[test]"

# Install all development dependencies
pip install -e ".[dev]"
```

---

## Key Capabilities & Algorithmic Modules

### Analytical Functions

- **`calculate_tmb()`**: Calculate Tumor Mutational Burden (TMB).

  TMB = Total mutations / Coding region size (Mb)

  Parameters: total_mutations, coding_region_size_mb, include_synonymous, synonymous_count

  Returns: dict with tmb, tmb_category, fda_eligible, coding_region_size_mb,
  total_mutations, non_synonymous_mutations, description

- **`adjust_for_panel_size()`**: Adjust TMB for small panel sizes using a correction factor.

  Small gene panels may over- or under-estimate TMB compared to WES.
  A correction factor is applied based on the ratio of panel size
  to reference (WES) size.

  Parameters: tmb_raw, panel_size_mb, reference_size_mb (default: WES = 38 Mb)

  Returns: dict with raw_tmb, adjusted_tmb, correction_factor, panel_size, reference_size

- **`immunotherapy_response_assessment()`**: Assess immunotherapy response likelihood based on TMB.

  Parameters: tmb, cancer_type (optional)

  Returns: dict with tmb, response_likelihood, therapy_recommendation, evidence_level

- **`get_panel_info()`**: Get information about a specific gene panel.
- **`process_batch()`**: Process a CSV of TMB cases.

---

## CLI Quickstart & Usage

### 1. Calculate TMB
```bash
python cli.py calc --mutations 380 --region-mb 38.0
```

### 2. Panel-adjusted TMB
```bash
python cli.py panel --mutations 15 --panel foundationone_cdx
```

### 3. Immunotherapy Response Assessment
```bash
python cli.py immune --tmb 12.0 --cancer-type NSCLC
```

### 4. Panel Information
```bash
python cli.py panel-info --name msk_impact
```

### 5. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 6. Enterprise Supervisor Audit
```bash
python cli.py audit --task-id TASK-001 --primary 29.4 --secondary 14.8 --status DISCORDANT_ANOMALY --critical
```

### 7. Supervisory Chat
```bash
python cli.py chat "Explain TMB thresholds for immunotherapy"
```

### 8. Verify Audit Trail
```bash
python cli.py verify-audit
```

### Parameter Reference
- `calc`: `--mutations`, `--region-mb`, `--include-synonymous`, `--synonymous-count`
- `panel`: `--mutations`, `--panel`, `--include-synonymous`, `--synonymous-count`
- `immune`: `--tmb`, `--cancer-type`
- `panel-info`: `--name`
- `batch`: `-i/--input`, `-o/--output`
- `audit`: `--task-id`, `--target`, `--primary`, `--secondary`, `--status`, `--critical`
- `chat`: positional query arguments
- `verify-audit`: no arguments

---

## Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB patterns, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable in production to ensure tamper-evident audit integrity:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key-min-16-chars"
```

---

## Testing & Verification

Run the full automated test suite:

```bash
pytest -v
```

Run specific test files:

```bash
pytest test_tmb_calc.py -v
pytest tests/ -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## Container Deployment

```bash
docker build -t tmb-tumor-mutation-burden-calc .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key tmb-tumor-mutation-burden-calc
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## Project Structure

```
tmb-tumor-mutation-burden-calc/
├── tmb_calc.py          # Core TMB calculation + CLI
├── cli.py               # CLI entry point
├── enrichment.py        # Enrichment feature engines
├── simulator.py         # High-throughput stress testing
├── agents/              # Enterprise supervisor & workers
│   ├── base.py          # PHI guard, HMAC audit trail
│   ├── models.py        # Pydantic schemas
│   ├── supervisor.py    # Multi-agent orchestrator
│   ├── workers.py       # Specialized domain workers
│   ├── api.py           # FastAPI REST endpoints
│   ├── llm_factory.py   # LLM provider abstraction
│   ├── learning.py      # Bayesian calibration engine
│   ├── metrics.py       # Prometheus metrics exporter
│   └── streamer.py      # WebSocket telemetry broadcaster
├── tests/               # Test suite
├── web/index.html       # Operations console UI
├── Dockerfile           # Container build
├── docker-compose.yml   # Container orchestration
├── pyproject.toml       # Project metadata & dependencies
└── openapi_spec.json    # OpenAPI 3.1 specification
```
