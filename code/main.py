"""main.py — synchronous pipeline orchestrator. Run with: python main.py"""

import time
from pathlib import Path

import pandas as pd

from config import (
    BASE_DIR, CLAIMS_CSV, OUTPUT_CSV,
    USER_HISTORY_CSV, EVIDENCE_REQUIREMENTS_CSV,
)
from utils.csv_utils import (
    load_claims, load_user_history,
    load_evidence_requirements, append_output_row,
)
from modules.image_analyzer import analyze_images
from modules.claim_extractor import extract_claim
from modules.normalizer import normalize_image_result, normalize_claim_result
from modules.evidence_checker import check_evidence
from modules.risk_analyzer import analyze_risk
from modules.decision_engine import decide
from models.schemas import OutputRow


def build_output_row(
    claim: pd.Series,
    decision,
    evidence_result,
) -> dict:
    """Assemble the final output dict from all pipeline results."""
    risk_flags = decision.all_risk_flags
    risk_str = ";".join(risk_flags) if risk_flags else "none"

    supporting = decision.supporting_image_ids
    supporting_str = ";".join(supporting) if supporting else "none"

    row = OutputRow(
        user_id=claim["user_id"],
        image_paths=claim["image_paths"],
        user_claim=claim["user_claim"],
        claim_object=claim["claim_object"],
        evidence_standard_met=str(evidence_result.evidence_standard_met).lower(),
        evidence_standard_met_reason=evidence_result.evidence_standard_met_reason,
        risk_flags=risk_str,
        issue_type=decision.issue_type,
        object_part=decision.object_part,
        claim_status=decision.claim_status,
        claim_status_justification=decision.claim_status_justification,
        supporting_image_ids=supporting_str,
        valid_image=str(decision.valid_image).lower(),
        severity=decision.severity,
    )
    return row.model_dump()


def process_claim(
    claim: pd.Series,
    user_history: dict,
    requirements: list[dict],
) -> dict:
    """Run the full pipeline for a single claim row."""
    user_id = claim["user_id"]
    image_paths_str = claim["image_paths"]
    user_claim = claim["user_claim"]
    claim_object = claim["claim_object"]

    print(f"  [1/5] Analyzing images for {user_id}...")
    image_results = analyze_images(
        user_id=user_id,
        image_paths_str=image_paths_str,
        claim_object=claim_object,
        base_dir=BASE_DIR,
    )

    print(f"  [2/5] Extracting claim for {user_id}...")
    claim_result = extract_claim(
        user_id=user_id,
        user_claim=user_claim,
        claim_object=claim_object,
    )

    print(f"  [3/5] Normalizing outputs for {user_id}...")
    image_results = [
        normalize_image_result(r, claim_object) for r in image_results
    ]
    claim_result = normalize_claim_result(claim_result, claim_object)

    print(f"  [4/5] Checking evidence + risk for {user_id}...")
    # Use best valid image's issue_type for evidence check
    valid_issues = [
        r.issue_type for r in image_results
        if r.valid_image and r.issue_type not in ("unknown", "none")
    ]
    issue_for_evidence = valid_issues[0] if valid_issues else claim_result.claimed_issue

    evidence_result = check_evidence(
        image_results=image_results,
        claim_object=claim_object,
        issue_type=issue_for_evidence,
        requirements=requirements,
    )
    risk_result = analyze_risk(
        user_id=user_id,
        user_history=user_history,
    )

    print(f"  [5/5] Making decision for {user_id}...")
    decision = decide(
        image_results=image_results,
        claim_result=claim_result,
        evidence_result=evidence_result,
        risk_result=risk_result,
        claim_object=claim_object,
    )

    return build_output_row(claim, decision, evidence_result)


def run(input_csv: Path, output_csv: Path) -> None:
    """Process all claims and write output row by row."""
    print(f"\n{'='*50}")
    print(f"Loading data from {input_csv.name}...")
    claims_df = load_claims(input_csv)
    user_history = load_user_history(USER_HISTORY_CSV)
    requirements = load_evidence_requirements(EVIDENCE_REQUIREMENTS_CSV)

    # Clear existing output file
    if output_csv.exists():
        output_csv.unlink()

    total = len(claims_df)
    print(f"Processing {total} claims...\n")
    start = time.time()

    for idx, (_, claim) in enumerate(claims_df.iterrows(), 1):
        print(f"[{idx}/{total}] Processing {claim['user_id']}...")
        try:
            row = process_claim(claim, user_history, requirements)
            append_output_row(output_csv, row)
            print(f"  ✓ Done → {row['claim_status']}\n")
        except Exception as e:
            print(f"  ✗ FAILED for {claim['user_id']}: {e}\n")
            # Write a safe fallback row so we don't lose the claim
            fallback = {
                "user_id": claim["user_id"],
                "image_paths": claim["image_paths"],
                "user_claim": claim["user_claim"],
                "claim_object": claim["claim_object"],
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": "Processing error.",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": f"System error: {str(e)[:100]}",
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown",
            }
            append_output_row(output_csv, fallback)

    elapsed = time.time() - start
    print(f"{'='*50}")
    print(f"Done. {total} claims processed in {elapsed:.1f}s")
    print(f"Output written to: {output_csv}")


if __name__ == "__main__":
    run(CLAIMS_CSV, OUTPUT_CSV)