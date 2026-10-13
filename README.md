# Tumor Mutational Burden (TMB) Calculator

A small Python and browser research utility for calculating tumor mutational burden (TMB) as eligible somatic mutations divided by the effective interrogated/callable genomic territory in megabases.

## Functions

- **Browser calculator:** enter eligible somatic mutation count, callable megabases and optional synonymous count. The browser performs all calculations locally, without uploading input or requiring Python.
- **Batch CSV:** process UTF-8 CSV files with total_mutations and coding_region_size_mb columns. The browser supports up to 2 MB/10,000 rows; Python processes local files without a fixed record limit.
- **Python API/CLI:** calculate TMB, return illustrative ranges, look up sample panel sizes, and provide exploratory immunotherapy context.
- **Optional FastAPI service:** serves the browser calculator plus research supervisor demonstration endpoints and an in-memory HMAC-chained audit log.

**TMB = eligible somatic mutations / eligible sequenced territory (Mb)**. Use the same assay-specific inclusion/filtering rules for numerator and denominator. Outputs are rounded to two decimals for display, but threshold comparisons use the unrounded ratio. The illustrative categories used by this program are Low (<5), Intermediate (5–<10), High (10–<16), Very high (≥16).

**Clinical limitations:** A numeric TMB ≥10 mut/Mb **does not establish pembrolizumab eligibility**. The FDA's June 2020 accelerated approval applies to specified unresectable/metastatic previously treated solid tumors with no satisfactory alternatives, assessed using an FDA-approved test. Assay selection, mutation filtering, panel content, effective genomic territory and clinical context all matter. The legacy result key fda_eligible is preserved for compatibility but means *numeric threshold met only*; prefer meets_numeric_fda_tmb_cutoff. No treatment recommendation is made by this program.

The historical size-only panel multiplier is scientifically unvalidated and **off by default**. Use adjust_for_panel_size(..., experimental_correction=True) only to reproduce legacy exploratory calculations, never to calibrate a patient result. Illustrative panel-size values are not a substitute for a verified assay specification.

Sources: [FDA approval notice](https://www.fda.gov/drugs/drug-approvals-and-databases/fda-approves-pembrolizumab-adults-and-children-tmb-h-solid-tumors); [Friends of Cancer Research TMB Harmonization, phase II](https://pubmed.ncbi.nlm.nih.gov/34606929/).

## Run locally

Requirements: Python 3.10+.

    python -m pip install -e ".[dev]"
    python cli.py calc --mutations 380 --region-mb 38
    python cli.py batch -i sample.csv -o results.csv
    python -m pytest -q
    node --test web/app.test.js

To use the browser independently, open web/index.html (modern evergreen browser). For local FastAPI service:

    python -m pip install -e ".[api]"
    uvicorn agents.api:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000/ for the calculator, http://127.0.0.1:8000/docs for generated API documentation. The demo supervisor's audit/chat/metrics endpoints do not provide clinical decision support. /metrics emits JSON, not Prometheus exposition text. Chat uses a deterministic mock, not a connected LLM.

Docker:

    export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    export AUDIT_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    docker compose up --build

Audit logs are available at GET /api/audit/logs only with an X-Audit-Token header matching AUDIT_API_TOKEN. The chain is signed in memory; it is not durable across process restarts. An unset AUDIT_SECRET_KEY uses a random temporary key, suitable for testing but not durable auditing. Protect all externally exposed FastAPI endpoints with an appropriate authentication/reverse-proxy layer; neither the supervisor demo nor the PHI pattern filter is a comprehensive HIPAA privacy control.

## Data handling and deployment

The browser application performs single-sample and CSV calculations entirely client-side and has no telemetry or storage backend. It requires no Pyodide/PyScript runtime. Only the static web/ directory is eligible for GitHub Pages publication; Python and FastAPI must run in a Python-capable environment. The repository includes a Pages workflow, subject to GitHub Pages being enabled and deployment succeeding. Do not enter patient identifiers in the demonstration API. CSV export guards against common spreadsheet formula injection patterns.

## License

MIT. See [LICENSE](LICENSE).
