"""risk_analyzer.py — generate risk flags from user history. No LLM."""

from models.schemas import RiskAnalysisResult, UserHistory


def analyze_risk(
    user_id: str,
    user_history: dict[str, UserHistory],
) -> RiskAnalysisResult:
    """Generate risk flags from user_history lookup.

    Args:
        user_id:      The user submitting the claim.
        user_history: Dict of UserHistory models keyed by user_id.

    Returns:
        RiskAnalysisResult with risk_flags and history_summary.
    """
    record: UserHistory | None = user_history.get(user_id)

    if not record:
        return RiskAnalysisResult(
            risk_flags=[],
            history_summary="No historical claim data found for this user.",
        )

    risk_flags: list[str] = []

    # Pull flags already computed in the CSV
    raw_flags = record.history_flags
    if raw_flags and raw_flags.lower() != "none":
        for flag in raw_flags.split(";"):
            flag = flag.strip()
            if flag:
                risk_flags.append(flag)

    # Additional rules on typed integer fields
    if record.rejected_claim >= 2 and "user_history_risk" not in risk_flags:
        risk_flags.append("user_history_risk")

    if record.last_90_days_claim_count >= 3 and "user_history_risk" not in risk_flags:
        risk_flags.append("user_history_risk")

    if record.manual_review_claim >= 2 and "manual_review_required" not in risk_flags:
        risk_flags.append("manual_review_required")

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for f in risk_flags:
        if f not in seen:
            seen.add(f)
            deduped.append(f)

    return RiskAnalysisResult(
        risk_flags=deduped,
        history_summary=record.history_summary,
    )