"""csv_utils.py — load input CSVs and append output rows."""

import csv
from pathlib import Path
import pandas as pd


def load_claims(path: Path) -> pd.DataFrame:
    """Load claims.csv or sample_claims.csv into a DataFrame."""
    df = pd.read_csv(path, dtype=str).fillna("")
    return df


def load_user_history(path: Path) -> dict[str, dict]:
    """Load user_history.csv into a dict keyed by user_id."""
    df = pd.read_csv(path, dtype=str).fillna("")
    return {row["user_id"]: row.to_dict() for _, row in df.iterrows()}


def load_evidence_requirements(path: Path) -> list[dict]:
    """Load evidence_requirements.csv as a list of dicts."""
    df = pd.read_csv(path, dtype=str).fillna("")
    return df.to_dict(orient="records")


def append_output_row(path: Path, row: dict) -> None:
    """Append one result row to output.csv, creating headers if needed."""
    fieldnames = [
        "user_id", "image_paths", "user_claim", "claim_object",
        "evidence_standard_met", "evidence_standard_met_reason",
        "risk_flags", "issue_type", "object_part", "claim_status",
        "claim_status_justification", "supporting_image_ids",
        "valid_image", "severity",
    ]
    file_exists = path.exists() and path.stat().st_size > 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)