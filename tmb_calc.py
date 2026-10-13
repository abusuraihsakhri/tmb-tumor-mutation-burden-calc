#!/usr/bin/env python3
"""
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
"""

import argparse
import csv
import json
import math
import os
import sys
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard whole-exome coding region size in megabases
WES_CODING_REGION_MB = 38.0

# Common panel sizes in Mb (coding region covered)
PANEL_SIZES_MB = {
    "foundationone_cdx": 1.14,
    "foundationone": 1.14,
    "msk_impact": 1.22,
    "msk-impact": 1.22,
    "tempus_xt": 1.50,
    "tempus-xT": 1.50,
    "tempus": 1.50,
    "guardant360": 0.73,
    "guardant": 0.73,
    "f1cdx": 1.14,
    "wes": 38.0,
    "tso500": 1.70,
    "tso-500": 1.70,
}

# FDA-approved TMB threshold
FDA_TMB_THRESHOLD = 10.0  # mut/Mb


# ---------------------------------------------------------------------------
# TMB Calculation
# ---------------------------------------------------------------------------

def calculate_tmb(total_mutations: int, coding_region_size_mb: float,
                  include_synonymous: bool = False,
                  synonymous_count: int = 0) -> Dict[str, Any]:
    """
    Calculate Tumor Mutational Burden (TMB).

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
    """
    if type(total_mutations) is not int or total_mutations < 0:
        raise ValueError("total_mutations must be >= 0 and an integer")
    if isinstance(coding_region_size_mb, bool) or not isinstance(coding_region_size_mb, (int, float)) or not math.isfinite(coding_region_size_mb) or coding_region_size_mb <= 0:
        raise ValueError("coding_region_size_mb must be > 0 and finite")
    if type(synonymous_count) is not int or synonymous_count < 0:
        raise ValueError("synonymous_count must be >= 0 and an integer")
    if synonymous_count > total_mutations:
        raise ValueError("synonymous_count cannot exceed total_mutations")

    non_syn = total_mutations - synonymous_count if include_synonymous else total_mutations
    raw_tmb = total_mutations / coding_region_size_mb
    if not math.isfinite(raw_tmb):
        raise ValueError("Calculated TMB is not finite")
    tmb = round(raw_tmb, 2)

    # Never make cutoff decisions with display-rounded measurements.
    if raw_tmb < 5.0:
        category = "Low"
        description = f"TMB {tmb} mut/Mb: Low tumor mutational burden."
    elif raw_tmb < 10.0:
        category = "Intermediate"
        description = f"TMB {tmb} mut/Mb: Intermediate tumor mutational burden."
    elif raw_tmb < 16.0:
        category = "High"
        description = f"TMB {tmb} mut/Mb: High numerical TMB (FDA cutoff met; eligibility not determined)."
    else:
        category = "Very High"
        description = f"TMB {tmb} mut/Mb: Very high tumor mutational burden."

    fda_eligible = raw_tmb >= FDA_TMB_THRESHOLD  # Compatibility: numerical cutoff only

    return {
        "tmb": tmb,
        "tmb_unrounded": raw_tmb,
        "tmb_category": category,
        "fda_eligible": fda_eligible,
        "meets_numeric_fda_tmb_cutoff": fda_eligible,
        "clinical_eligibility_determined": False,
        "clinical_note": "Numerical cutoff does not establish clinical treatment eligibility; assay, stage, previous treatment and alternatives matter.",
        "fda_threshold": FDA_TMB_THRESHOLD,
        "coding_region_size_mb": coding_region_size_mb,
        "total_mutations": total_mutations,
        "non_synonymous_mutations": non_syn,
        "synonymous_mutations": synonymous_count if include_synonymous else "not specified",
        "include_synonymous": include_synonymous,
        "description": description,
    }


# ---------------------------------------------------------------------------
# Panel Size Adjustment
# ---------------------------------------------------------------------------

def adjust_for_panel_size(tmb_raw: float, panel_size_mb: float,
                          reference_size_mb: float = WES_CODING_REGION_MB,
                          experimental_correction: bool = False) -> Dict[str, Any]:
    """
    Adjust TMB for small panel sizes using a correction factor.

    Small gene panels may over- or under-estimate TMB compared to WES.
    By default this function leaves raw TMB unchanged. The old size-only
    heuristic is available only with experimental_correction=True.

    Size alone cannot calibrate panels; use validated assay-specific
    measurements for clinical analyses.

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
    """
    for name, value in (("tmb_raw", tmb_raw), ("panel_size_mb", panel_size_mb), ("reference_size_mb", reference_size_mb)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if value < 0 or (name != "tmb_raw" and value == 0):
            raise ValueError(f"{name} must be {'>= 0' if name == 'tmb_raw' else '> 0'}")

    # For small panels, apply a variance-based correction
    # Larger panels are more stable; smaller panels have higher variance
    # Simplified: correction = sqrt(reference / panel) for small panels
    if experimental_correction and panel_size_mb < 5.0:
        correction_factor = round((reference_size_mb / panel_size_mb) ** 0.15, 3)
    else:
        correction_factor = 1.0

    adjusted_tmb = round(tmb_raw * correction_factor, 2)

    return {
        "raw_tmb": tmb_raw,
        "adjusted_tmb": adjusted_tmb,
        "correction_factor": correction_factor,
        "panel_size_mb": panel_size_mb,
        "reference_size_mb": reference_size_mb,
        "experimental_correction": experimental_correction,
        "note": "Size-only correction is an unvalidated experimental heuristic; never use it for clinical eligibility or patient care.",
    }


# ---------------------------------------------------------------------------
# Immunotherapy Response Correlation
# ---------------------------------------------------------------------------

def immunotherapy_response_assessment(tmb: float, cancer_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Assess immunotherapy response likelihood based on TMB.

    Parameters
    ----------
    tmb : float
        TMB in mut/Mb.
    cancer_type : str, optional
        Cancer type for context-specific assessment.

    Returns
    -------
    dict with tmb, response_likelihood, therapy_recommendation, evidence_level
    """
    if isinstance(tmb, bool) or not isinstance(tmb, (int, float)) or not math.isfinite(tmb) or tmb < 0:
        raise ValueError("tmb must be a finite non-negative number")

    result = {"tmb": tmb}

    if tmb >= FDA_TMB_THRESHOLD:
        result["response_likelihood"] = "TMB at or above numeric high cutoff; response probability not determined"
        result["therapy_recommendation"] = (
            "FDA 2020 accelerated approval of Pembrolizumab concerns previously treated unresectable "
            "or metastatic solid tumors with TMB >=10 mut/Mb by an FDA-approved "
            "test and no satisfactory alternative treatments. "
            "This numerical assessment does not establish clinical eligibility."
        )
        result["evidence_level"] = "FDA indication applies only with its additional clinical and assay criteria"
    elif tmb >= 5.0:
        result["response_likelihood"] = "Intermediate TMB; response probability not determined"
        result["therapy_recommendation"] = (
            "TMB is intermediate. Response to checkpoint inhibitors varies by "
            "cancer type. Consider as part of a comprehensive biomarker panel."
        )
        result["evidence_level"] = "Descriptive TMB category; no response prediction"
    else:
        result["response_likelihood"] = "Low TMB; response probability not determined"
        result["therapy_recommendation"] = (
            "TMB is below this numeric cutoff. It does not exclude benefit "
            "from immunotherapy under other indications or biomarkers."
        )
        result["evidence_level"] = "Descriptive TMB category; no response prediction"

    result["note"] = "Exploratory context only; not a validated response predictor or a treatment recommendation."
    if cancer_type:
        result["cancer_type"] = cancer_type

    return result


# ---------------------------------------------------------------------------
# Panel Size Lookup
# ---------------------------------------------------------------------------

def get_panel_info(panel_name: str) -> Dict[str, Any]:
    """Get information about a specific gene panel."""
    key = panel_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    # Try exact match first, then normalized
    for k, v in PANEL_SIZES_MB.items():
        if k.lower().replace("-", "").replace("_", "") == key:
            return {"panel_name": panel_name, "coding_region_mb": v}

    valid = ", ".join(sorted(set(PANEL_SIZES_MB.keys())))
    raise ValueError(f"Unknown panel '{panel_name}'. Valid: {valid}")


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of TMB cases.

    Expected columns: total_mutations, coding_region_size_mb
    Optional: synonymous_count, include_synonymous, cancer_type
    """
    if os.path.realpath(input_csv) == os.path.realpath(output_csv):
        raise ValueError("Input and output CSV paths must differ")
    with open(input_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if not {"total_mutations", "coding_region_size_mb"}.issubset(fieldnames):
            raise ValueError("CSV requires total_mutations and coding_region_size_mb columns")
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("CSV contains duplicate column names")
        rows = list(reader)

    out_fields = fieldnames + [key for key in ("tmb", "tmb_category", "fda_eligible", "therapy_recommendation") if key not in fieldnames]
    out_rows = []

    for row_number, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"CSV row {row_number} contains extra columns")
        try:
            mutations = int(row["total_mutations"])
            region_mb = float(row["coding_region_size_mb"])
            syn_count = int(row.get("synonymous_count") or 0)
            flag = (row.get("include_synonymous") or "false").strip().lower()
            if flag not in ("true", "false", "yes", "no", "1", "0"):
                raise ValueError("include_synonymous must be true/false")
            include_syn = flag in ("true", "yes", "1")
            cancer = row.get("cancer_type", None)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid CSV row {row_number}: {exc}") from exc

        tmb_result = calculate_tmb(mutations, region_mb, include_syn, syn_count)
        response = immunotherapy_response_assessment(tmb_result["tmb"], cancer)

        row_dict = {key: ("'" + val if isinstance(val, str) and val.lstrip().startswith(("=", "+", "-", "@")) else val) for key, val in row.items()}
        row_dict["tmb"] = tmb_result["tmb"]
        row_dict["tmb_category"] = tmb_result["tmb_category"]
        row_dict["fda_eligible"] = tmb_result["fda_eligible"]
        row_dict["therapy_recommendation"] = response["therapy_recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Tumor Mutational Burden (TMB) Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Calculate TMB
    p_calc = subparsers.add_parser("calc", help="Calculate TMB")
    p_calc.add_argument("--mutations", type=int, required=True,
                         help="Total somatic mutations detected")
    p_calc.add_argument("--region-mb", type=float, required=True,
                         help="Coding region size in Mb")
    p_calc.add_argument("--include-synonymous", action="store_true",
                         help="Include synonymous mutations in count")
    p_calc.add_argument("--synonymous-count", type=int, default=0,
                         help="Number of synonymous mutations")

    # Panel-adjusted TMB
    p_panel = subparsers.add_parser("panel", help="Calculate TMB with panel adjustment")
    p_panel.add_argument("--mutations", type=int, required=True)
    p_panel.add_argument("--panel", required=True,
                          help="Panel name (e.g., foundationone_cdx, msk_impact)")
    p_panel.add_argument("--include-synonymous", action="store_true")
    p_panel.add_argument("--synonymous-count", type=int, default=0)

    # Immunotherapy assessment
    p_immune = subparsers.add_parser("immune", help="Assess immunotherapy response")
    p_immune.add_argument("--tmb", type=float, required=True,
                           help="TMB value in mut/Mb")
    p_immune.add_argument("--cancer-type", default=None,
                           help="Cancer type (optional)")

    # Panel info
    p_info = subparsers.add_parser("panel-info", help="Get panel information")
    p_info.add_argument("--name", required=True, help="Panel name")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Audit (enterprise supervisor dispatch)
    p_audit = subparsers.add_parser("audit", help="Dispatch task through enterprise supervisor")
    p_audit.add_argument("--task-id", required=True, help="Task identifier")
    p_audit.add_argument("--target", default="SPECIMEN-001", help="Target identifier")
    p_audit.add_argument("--primary", type=float, default=10.0, help="Primary metric")
    p_audit.add_argument("--secondary", type=float, default=3.0, help="Secondary metric")
    p_audit.add_argument("--status", default="NOMINAL", help="Status descriptor")
    p_audit.add_argument("--critical", action="store_true", help="Critical flag")

    # Chat (supervisory conversational assistant)
    p_chat = subparsers.add_parser("chat", help="Supervisory conversational assistant")
    p_chat.add_argument("query", nargs="+", help="Query text")

    # Verify audit trail integrity
    p_verify = subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    args = parser.parse_args(argv)

    if args.command == "calc":
        result = calculate_tmb(
            args.mutations, args.region_mb,
            args.include_synonymous, args.synonymous_count
        )
        print(json.dumps(result, indent=2))

    elif args.command == "panel":
        panel_info = get_panel_info(args.panel)
        result = calculate_tmb(
            args.mutations, panel_info["coding_region_mb"],
            args.include_synonymous, args.synonymous_count
        )
        result["panel"] = panel_info["panel_name"]
        print(json.dumps(result, indent=2))

    elif args.command == "immune":
        result = immunotherapy_response_assessment(args.tmb, args.cancer_type)
        print(json.dumps(result, indent=2))

    elif args.command == "panel-info":
        result = get_panel_info(args.name)
        print(json.dumps(result, indent=2))

    elif args.command == "batch":
        count = process_batch(args.input, args.output)
        print(f"Processed {count} records -> {args.output}")

    elif args.command == "audit":
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        supervisor = SystemSupervisor(model_provider="mock")
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"query": query, "response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        verified = AuditLogger.verify_integrity()
        trail_len = len(AuditLogger.get_trail())
        print(json.dumps({"audit_integrity_verified": verified, "trail_length": trail_len}, indent=2))

    return 0


if __name__ == "__main__":
    main()
