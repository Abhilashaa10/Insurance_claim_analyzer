"""risk_analyzer.py — generate risk flags from user history. No LLM."""

from models.schemas import RiskAnalysisResult


def analyze_risk(
    user_id: str,
    user_history: dict[str, dict],
) -> RiskAnalysisResult:
    """Generate risk flags from user_history.csv lookup.

    Args:
        user_id:      The user submitting the claim.
        user_history: Full history dict keyed by user_id.

    Returns:
        RiskAnalysisResult with risk_flags list and history_summary string.
    """
    record = user_history.get(user_id)

    if not record:
        return RiskAnalysisResult(
            risk_flags=[],
            history_summary="No historical claim data found for this user.",
        )

    risk_flags: list[str] = []

    # Pull raw history flags already computed in the CSV
    raw_flags = record.get("history_flags", "none")
    if raw_flags and raw_flags.lower() != "none":
        for flag in raw_flags.split(";"):
            flag = flag.strip()
            if flag:
                risk_flags.append(flag)

    # Additional rules based on numeric fields
    try:
        rejected = int(record.get("rejected_claim", 0))
        last_90 = int(record.get("last_90_days_claim_count", 0))
        past_total = int(record.get("past_claim_count", 0))
        manual = int(record.get("manual_review_claim", 0))
    except ValueError:
        rejected = last_90 = past_total = manual = 0

    if rejected >= 2 and "user_history_risk" not in risk_flags:
        risk_flags.append("user_history_risk")

    if last_90 >= 3 and "user_history_risk" not in risk_flags:
        risk_flags.append("user_history_risk")

    if manual >= 2 and "manual_review_required" not in risk_flags:
        risk_flags.append("manual_review_required")

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for f in risk_flags:
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    history_summary = record.get("history_summary", "")

    return RiskAnalysisResult(
        risk_flags=deduped,
        history_summary=history_summary,
    )