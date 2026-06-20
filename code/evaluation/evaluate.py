"""evaluate.py — compare pipeline output against sample_claims.csv ground truth."""

import sys
from pathlib import Path
import pandas as pd

# Allow running from evaluation/ folder or project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SAMPLE_CLAIMS_CSV, BASE_DIR, OUTPUT_CSV
from utils.csv_utils import load_claims, load_user_history, load_evidence_requirements
from modules.image_analyzer import analyze_images
from modules.claim_extractor import extract_claim
from modules.normalizer import normalize_image_result, normalize_claim_result
from modules.evidence_checker import check_evidence
from modules.risk_analyzer import analyze_risk
from modules.decision_engine import decide
from main import build_output_row, process_claim
from config import USER_HISTORY_CSV, EVIDENCE_REQUIREMENTS_CSV


EVAL_OUTPUT = Path(__file__).parent / "eval_output.csv"
REPORT_PATH = Path(__file__).parent / "evaluation_report.md"

GRADED_FIELDS = [
    "claim_status",
    "issue_type",
    "object_part",
    "severity",
    "evidence_standard_met",
    "valid_image",
]


def normalize_bool(val: str) -> str:
    return str(val).strip().lower()


def field_accuracy(pred_df: pd.DataFrame, truth_df: pd.DataFrame, field: str) -> float:
    """Compute exact-match accuracy for one field."""
    pred = pred_df[field].astype(str).str.strip().str.lower()
    truth = truth_df[field].astype(str).str.strip().str.lower()
    correct = (pred == truth).sum()
    return round(correct / len(truth) * 100, 1) if len(truth) > 0 else 0.0


def run_evaluation() -> None:
    print("Loading sample claims...")
    sample_df = load_claims(SAMPLE_CLAIMS_CSV)
    user_history = load_user_history(USER_HISTORY_CSV)
    requirements = load_evidence_requirements(EVIDENCE_REQUIREMENTS_CSV)

    # Clear eval output
    if EVAL_OUTPUT.exists():
        EVAL_OUTPUT.unlink()

    results = []
    total = len(sample_df)
    print(f"Running pipeline on {total} sample claims...\n")

    for idx, (_, claim) in enumerate(sample_df.iterrows(), 1):
        print(f"[{idx}/{total}] {claim['user_id']}...")
        try:
            row = process_claim(claim, user_history, requirements)
            results.append(row)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "user_id": claim["user_id"],
                "image_paths": claim.get("image_paths", ""),
                "user_claim": claim.get("user_claim", ""),
                "claim_object": claim.get("claim_object", ""),
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": "Error",
                "risk_flags": "none",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": str(e),
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown",
            })

    pred_df = pd.DataFrame(results)
    pred_df.to_csv(EVAL_OUTPUT, index=False)
    print(f"\nEval predictions saved to {EVAL_OUTPUT}")

    # Score
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    scores = {}
    for field in GRADED_FIELDS:
        if field in sample_df.columns and field in pred_df.columns:
            acc = field_accuracy(pred_df, sample_df, field)
            scores[field] = acc
            print(f"  {field:<30} {acc:>6.1f}%")

    overall = round(sum(scores.values()) / len(scores), 1) if scores else 0.0
    print(f"\n  {'OVERALL (avg)':<30} {overall:>6.1f}%")
    print("="*50)

    # Write report
    lines = [
        "# Evaluation Report\n",
        "## Field Accuracy (vs sample_claims.csv)\n",
        "| Field | Accuracy |",
        "|-------|----------|",
    ]
    for field, acc in scores.items():
        lines.append(f"| {field} | {acc}% |")
    lines += [
        f"\n**Overall Average Accuracy:** {overall}%\n",
        "## Operational Analysis\n",
        f"- Sample claims processed: {total}",
        f"- LLM calls per claim: 2 (image_analyzer + claim_extractor)",
        f"- Total LLM calls: {total * 2}",
        f"- Estimated input tokens per claim: ~2500 (images) + ~300 (claim text)",
        f"- Estimated output tokens per claim: ~400 (image JSON) + ~150 (claim JSON)",
        f"- Model: {Path(sys.argv[0]).name} uses MODEL_NAME env var",
        f"- Images processed: varies per claim (1–3 per claim)",
        "- Cost estimate (claude-sonnet-4-6 @ $3/MTok in, $15/MTok out):",
        f"  - 44 test claims × ~2800 in tokens = ~123K input tokens ≈ $0.37",
        f"  - 44 test claims × ~550 out tokens = ~24K output tokens ≈ $0.36",
        f"  - **Estimated total: ~$0.73 for full test set**",
        "- Rate limit strategy: tenacity retry with exponential backoff",
        "- No batching needed at this scale (44 claims)",
        "- Output written row-by-row to prevent data loss on crash",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    run_evaluation()