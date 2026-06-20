"""decision_engine.py — deterministic rules to produce final claim decision."""

from models.schemas import (
    ImageAnalysisResult,
    ClaimExtractionResult,
    EvidenceCheckResult,
    RiskAnalysisResult,
    DecisionResult,
)
from config import CONFIDENCE_THRESHOLD


def _select_best_image(
    image_results: list[ImageAnalysisResult],
) -> ImageAnalysisResult | None:
    """Return the valid image with highest overall confidence."""
    valid = [r for r in image_results if r.valid_image]
    if not valid:
        return None
    return max(valid, key=lambda r: r.confidence.overall)


def _select_supporting_images(
    image_results: list[ImageAnalysisResult],
    claim_status: str,
    issue_type: str,
) -> list[str]:
    """Return image IDs that actually support the decision.

    For supported: images showing the claimed damage.
    For contradicted: images showing no damage or wrong object.
    For not_enough_information: empty.
    """
    if claim_status == "not_enough_information":
        return []

    supporting = []
    for r in image_results:
        if not r.valid_image:
            continue
        if claim_status == "supported" and r.issue_type == issue_type:
            supporting.append(r.image_id)
        elif claim_status == "contradicted":
            if r.issue_type in ("none", "unknown") or not r.matches_claim_object:
                supporting.append(r.image_id)
    return supporting


def _all_risk_flags(
    image_results: list[ImageAnalysisResult],
    risk_result: RiskAnalysisResult,
) -> list[str]:
    """Merge image-level and user-history risk flags, deduplicated."""
    seen: set[str] = set()
    merged: list[str] = []
    for r in image_results:
        for f in r.risk_flags:
            if f not in seen:
                seen.add(f)
                merged.append(f)
    for f in risk_result.risk_flags:
        if f not in seen:
            seen.add(f)
            merged.append(f)
    return merged


def _any_valid(image_results: list[ImageAnalysisResult]) -> bool:
    return any(r.valid_image for r in image_results)


def _images_show_damage(
    image_results: list[ImageAnalysisResult],
) -> bool:
    """True if at least one valid image shows a real damage type."""
    no_damage = {"none", "unknown"}
    return any(
        r.valid_image and r.issue_type not in no_damage
        for r in image_results
    )


def _object_matches(
    image_results: list[ImageAnalysisResult],
    claim_object: str,
) -> bool:
    return any(
        r.valid_image and r.detected_object == claim_object
        for r in image_results
    )


def decide(
    image_results: list[ImageAnalysisResult],
    claim_result: ClaimExtractionResult,
    evidence_result: EvidenceCheckResult,
    risk_result: RiskAnalysisResult,
    claim_object: str,
) -> DecisionResult:
    """Apply deterministic decision rules.

    Priority: Visual Evidence > Claim Text > User History.

    Rules (in order):
    1. No valid images → not_enough_information
    2. Evidence standard not met → not_enough_information
    3. No valid image shows claimed object → not_enough_information
    4. Low overall confidence → not_enough_information
    5. Image shows no damage for claimed part → contradicted
    6. Image damage matches claim → supported
    7. Image damage does not match claim → contradicted
    8. Default → not_enough_information
    """
    all_flags = _all_risk_flags(image_results, risk_result)
    best = _select_best_image(image_results)
    overall_valid = _any_valid(image_results)

    # Rule 1: no valid images
    if not overall_valid or best is None:
        return DecisionResult(
            claim_status="not_enough_information",
            claim_status_justification=(
                "No valid images were provided. Cannot evaluate the claim."
            ),
            supporting_image_ids=[],
            issue_type="unknown",
            object_part="unknown",
            severity="unknown",
            valid_image=False,
            all_risk_flags=all_flags,
        )

    # Rule 2: evidence standard not met
    if not evidence_result.evidence_standard_met:
        return DecisionResult(
            claim_status="not_enough_information",
            claim_status_justification=(
                f"Evidence standard not met. "
                f"{evidence_result.evidence_standard_met_reason}"
            ),
            supporting_image_ids=[],
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity=best.severity,
            valid_image=True,
            all_risk_flags=all_flags,
        )

    # Rule 3: object mismatch
    if not _object_matches(image_results, claim_object):
        ids = _select_supporting_images(image_results, "contradicted", best.issue_type)
        return DecisionResult(
            claim_status="contradicted",
            claim_status_justification=(
                f"Images do not show a {claim_object}. "
                f"Detected: {best.detected_object}. "
                f"Claim cannot be verified."
            ),
            supporting_image_ids=ids,
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity=best.severity,
            valid_image=True,
            all_risk_flags=["wrong_object"] + [f for f in all_flags if f != "wrong_object"],
        )

    # Rule 4: low confidence fallback
    if best.confidence.overall < CONFIDENCE_THRESHOLD:
        return DecisionResult(
            claim_status="not_enough_information",
            claim_status_justification=(
                f"Image confidence too low ({best.confidence.overall:.2f}) "
                f"to make a reliable decision. Manual review recommended."
            ),
            supporting_image_ids=[],
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity=best.severity,
            valid_image=True,
            all_risk_flags=all_flags + ["manual_review_required"],
        )

    # Rule 5: part visible, no damage → contradicted
    no_damage_types = {"none"}
    if best.issue_type in no_damage_types and best.object_part != "unknown":
        ids = _select_supporting_images(image_results, "contradicted", best.issue_type)
        return DecisionResult(
            claim_status="contradicted",
            claim_status_justification=(
                f"{best.image_id} shows the {best.object_part} clearly "
                f"with no visible damage, contradicting the claim of "
                f"{claim_result.claimed_issue}."
            ),
            supporting_image_ids=ids,
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity="none",
            valid_image=True,
            all_risk_flags=all_flags,
        )

    # Rule 6: damage visible and matches claimed issue
    if (
        _images_show_damage(image_results)
        and best.issue_type == claim_result.claimed_issue
    ):
        ids = _select_supporting_images(image_results, "supported", best.issue_type)
        return DecisionResult(
            claim_status="supported",
            claim_status_justification=(
                f"{best.image_id} shows visible {best.issue_type} "
                f"on the {best.object_part}, consistent with the reported claim."
            ),
            supporting_image_ids=ids or [best.image_id],
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity=best.severity,
            valid_image=True,
            all_risk_flags=all_flags,
        )

    # Rule 7: damage visible but does not match claim
    if _images_show_damage(image_results):
        ids = _select_supporting_images(image_results, "contradicted", best.issue_type)
        return DecisionResult(
            claim_status="contradicted",
            claim_status_justification=(
                f"{best.image_id} shows {best.issue_type} on the "
                f"{best.object_part}, but the claim states "
                f"{claim_result.claimed_issue} on "
                f"{claim_result.claimed_part}. Visual evidence does not match."
            ),
            supporting_image_ids=ids or [best.image_id],
            issue_type=best.issue_type,
            object_part=best.object_part,
            severity=best.severity,
            valid_image=True,
            all_risk_flags=all_flags,
        )

    # Rule 8: default
    return DecisionResult(
        claim_status="not_enough_information",
        claim_status_justification=(
            "Could not determine claim status from the available images."
        ),
        supporting_image_ids=[],
        issue_type=best.issue_type,
        object_part=best.object_part,
        severity=best.severity,
        valid_image=True,
        all_risk_flags=all_flags,
    )