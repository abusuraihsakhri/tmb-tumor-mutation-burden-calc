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
    "wgs": 38.0,
    "tso500": 1.70,
    "tso-500": 1.70,
    "nextseq": 1.70,
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
    if total_mutations < 0:
        raise ValueError(f"total_mutations must be >= 0; got {total_mutations}")
    if coding_region_size_mb <= 0:
        raise ValueError(f"coding_region_size_mb must be > 0; got {coding_region_size_mb}")
    if synonymous_count < 0:
        raise ValueError(f"synonymous_count must be >= 0; got {synonymous_count}")
    if synonymous_count > total_mutations:
        raise ValueError("synonymous_count cannot exceed total_mutations")

    non_syn = total_mutations - synonymous_count if include_synonymous else total_mutations
    tmb = round(total_mutations / coding_region_size_mb, 2)

    # Category thresholds
    if tmb < 5.0:
        category = "Low"
        description = f"TMB {tmb} mut/Mb: Low tumor mutational burden."
    elif tmb < 10.0:
        category = "Intermediate"
        description = f"TMB {tmb} mut/Mb: Intermediate tumor mutational burden."
    elif tmb < 16.0:
        category = "High"
        description = f"TMB {tmb} mut/Mb: High tumor mutational burden (FDA threshold met)."
    else:
        category = "Very High"
        description = f"TMB {tmb} mut/Mb: Very high tumor mutational burden."

    fda_eligible = tmb >= FDA_TMB_THRESHOLD

    return {
        "tmb": tmb,
        "tmb_category": category,
        "fda_eligible": fda_eligible,
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
                          reference_size_mb: float = WES_CODING_REGION_MB) -> Dict[str, Any]:
    """
    Adjust TMB for small panel sizes using a correction factor.

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
    """
    if tmb_raw < 0:
        raise ValueError(f"tmb_raw must be >= 0; got {tmb_raw}")
    if panel_size_mb <= 0:
        raise ValueError(f"panel_size_mb must be > 0; got {panel_size_mb}")
    if reference_size_mb <= 0:
        raise ValueError(f"reference_size_mb must be > 0; got {reference_size_mb}")

    # For small panels, apply a variance-based correction
    # Larger panels are more stable; smaller panels have higher variance
    # Simplified: correction = sqrt(reference / panel) for small panels
    if panel_size_mb < 5.0:
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
        "note": "Panel-specific validation data should be used when available.",
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
    if tmb < 0:
        raise ValueError(f"tmb must be >= 0; got {tmb}")

    result = {"tmb": tmb}

    if tmb >= FDA_TMB_THRESHOLD:
        result["response_likelihood"] = "Higher likelihood of response to checkpoint inhibitors"
        result["therapy_recommendation"] = (
            "Pembrolizumab approved for TMB-H (>=10 mut/Mb) solid tumors "
            "regardless of cancer type (FDA 2020). Consider immune checkpoint "
            "inhibitor therapy."
        )
        result["evidence_level"] = "FDA-approved (KEYNOTE-158)"
    elif tmb >= 5.0:
        result["response_likelihood"] = "Moderate likelihood of response"
        result["therapy_recommendation"] = (
            "TMB is intermediate. Response to checkpoint inhibitors varies by "
            "cancer type. Consider as part of a comprehensive biomarker panel."
        )
        result["evidence_level"] = "Emerging evidence"
    else:
        result["response_likelihood"] = "Lower likelihood of response to checkpoint inhibitors alone"
        result["therapy_recommendation"] = (
            "TMB is low. Checkpoint inhibitor monotherapy may have limited "
            "efficacy. Consider combination therapy or alternative approaches."
        )
        result["evidence_level"] = "Standard of care"

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
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + ["tmb", "tmb_category", "fda_eligible",
                               "therapy_recommendation"]
    out_rows = []

    for row in rows:
        mutations = int(row.get("total_mutations", 0))
        region_mb = float(row.get("coding_region_size_mb", WES_CODING_REGION_MB))
        syn_count = int(row.get("synonymous_count", 0))
        include_syn = row.get("include_synonymous", "false").lower() == "true"
        cancer = row.get("cancer_type", None)

        tmb_result = calculate_tmb(mutations, region_mb, include_syn, syn_count)
        response = immunotherapy_response_assessment(tmb_result["tmb"], cancer)

        row_dict = dict(row)
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
