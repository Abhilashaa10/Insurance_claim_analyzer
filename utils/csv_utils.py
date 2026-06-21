"""csv_utils.py — load input CSVs and append output rows."""

import csv
from pathlib import Path

import pandas as pd

from models.schemas import UserHistory


def load_claims(path: Path) -> pd.DataFrame:
    """Load claims.csv or sample_claims.csv into a DataFrame."""
    return pd.read_csv(path, dtype=str).fillna("")


def load_user_history(path: Path) -> dict[str, UserHistory]:
    """Load user_history.csv into a dict of UserHistory models keyed by user_id."""
    df = pd.read_csv(path, dtype=str).fillna("0")
    result: dict[str, UserHistory] = {}
    for _, row in df.iterrows():
        uid = row["user_id"]
        result[uid] = UserHistory(
            user_id=uid,
            past_claim_count=int(row.get("past_claim_count", 0)),
            accept_claim=int(row.get("accept_claim", 0)),
            manual_review_claim=int(row.get("manual_review_claim", 0)),
            rejected_claim=int(row.get("rejected_claim", 0)),
            last_90_days_claim_count=int(row.get("last_90_days_claim_count", 0)),
            history_flags=str(row.get("history_flags", "none")),
            history_summary=str(row.get("history_summary", "")),
        )
    return result


def load_evidence_requirements(path: Path) -> list[dict]:
    """Load evidence_requirements.csv as a list of dicts."""
    return pd.read_csv(path, dtype=str).fillna("").to_dict(orient="records")


def append_output_row(path: Path, row: dict) -> None:
    """Append one result row to output.csv, creating headers if file is new."""
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