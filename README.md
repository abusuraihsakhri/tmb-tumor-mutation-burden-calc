# TMB Tumor Mutation Burden Calc

> **Domain:** Medical Oncology & Cancer Staging Systems  
> **Reference Guidelines & Standards:** `AJCC Cancer Staging Manual & NCCN Clinical Practice Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Tumor Mutational Burden (TMB) Calculator

Calculates somatic mutations per megabase (mut/Mb) from targeted gene panels
or whole-exome sequencing (WES) with FDA-approved thresholds.

References:
  - Marabelle A et al. Lancet Oncol. 2020;21(1):71-82 (KEYNOTE-158 TMB-H)
  - FDA Approval: Pembrolizumab for TMB-H (>=10 mut/Mb) solid tumors (June 2020)
  - Stenzinger A et al. J Immunother Cancer. 2019;7(1):185 (TMB harmonization)
  - Chalmers ZR et al. Genome Med. 2017;9(1):34 (FoundationOne CDx panel)

Zero-dependency Python implementation (stdlib only).
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_tmb()`**: Calculate Tumor Mutational Burden (TMB).

TMB = Total mutations / Coding region size (Mb)

Parameters
----------
total_mutations : int
    Total number of somatic mutations detected.
coding_region_size_mb : float
    Size of the coding region in megabases (Mb).
include_synonymous : bool
    Whether synonymous mutations are included in total_mutations.
synonymous_count : int
    Number of synonymous mutations (used for reporting only).

Returns
-------
dict with tmb, tmb_category, fda_eligible, coding_region_size_mb,
total_mutations, non_synonymous_mutations, description
- **`adjust_for_panel_size()`**: Adjust TMB for small panel sizes using a correction factor.

Small gene panels may over- or under-estimate TMB compared to WES.
A correction factor can be applied based on the ratio of panel size
to reference (WES) size.

Note: This is a simplified linear correction. In practice, panel-specific
correction factors from validation studies should be used.

Parameters
----------
tmb_raw : float
    Raw TMB calculated from the panel.
panel_size_mb : float
    Panel coding region size in Mb.
reference_size_mb : float
    Reference size (default: WES = 38 Mb).

Returns
-------
dict with raw_tmb, adjusted_tmb, correction_factor, panel_size, reference_size
- **`immunotherapy_response_assessment()`**: Assess immunotherapy response likelihood based on TMB.

Parameters
----------
tmb : float
    TMB in mut/Mb.
cancer_type : str, optional
    Cancer type for context-specific assessment.

Returns
-------
dict with tmb, response_likelihood, therapy_recommendation, evidence_level
- **`get_panel_info()`**: Get information about a specific gene panel.
- **`process_batch()`**: Process a CSV of TMB cases.

Expected columns: total_mutations, coding_region_size_mb
Optional: synonymous_count, include_synonymous, cancer_type

---

## 📐 Mathematical Formulation & Logic

```text
  Calculates somatic mutations per megabase (mut/Mb) from targeted gene panels
  Calculate Tumor Mutational Burden (TMB).
  Raw TMB calculated from the panel.
  tmb_result = calculate_tmb(mutations, region_mb, include_syn, syn_count)
  Calculate TMB
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t tmb-tumor-mutation-burden-calc .
docker run -p 8000:8000 tmb-tumor-mutation-burden-calc
```
