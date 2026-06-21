"""evidence_checker.py — Python lookup against evidence_requirements.csv."""

from models.schemas import ImageAnalysisResult, EvidenceCheckResult

# Maps issue_type → requirement applies_to keywords for matching
ISSUE_TO_APPLIES: dict[str, list[str]] = {
    "dent":              ["dent", "scratch", "body panel"],
    "scratch":           ["dent", "scratch", "body panel"],
    "crack":             ["crack", "broken", "missing", "glass", "light", "mirror"],
    "glass_shatter":     ["crack", "broken", "missing", "glass", "light", "mirror"],
    "broken_part":       ["crack", "broken", "missing", "glass", "light", "mirror"],
    "missing_part":      ["crack", "broken", "missing", "glass", "light", "mirror"],
    "water_damage":      ["water", "stain", "label"],
    "stain":             ["water", "stain", "label"],
    "torn_packaging":    ["crushed", "torn", "seal", "exterior"],
    "crushed_packaging": ["crushed", "torn", "seal", "exterior"],
    "none":              ["general"],
    "unknown":           ["general"],
}


def _requirement_applies(req: dict, claim_object: str, issue_type: str) -> bool:
    """Check whether a requirement row applies to this claim."""
    obj_match = req["claim_object"] in ("all", claim_object)
    if not obj_match:
        return False
    keywords = ISSUE_TO_APPLIES.get(issue_type, ["general"])
    applies_to = req["applies_to"].lower()
    return any(kw in applies_to for kw in keywords)


def _any_valid_image(image_results: list[ImageAnalysisResult]) -> bool:
    return any(r.valid_image for r in image_results)


def _any_matching_object(
    image_results: list[ImageAnalysisResult],
    claim_object: str,
) -> bool:
    return any(
        r.detected_object == claim_object and r.valid_image
        for r in image_results
    )


def check_evidence(
    image_results: list[ImageAnalysisResult],
    claim_object: str,
    issue_type: str,
    requirements: list[dict],
) -> EvidenceCheckResult:
    """Determine whether submitted images meet the minimum evidence standard.

    Logic (in order):
    1. At least one valid image must exist.
    2. At least one valid image must show the claimed object.
    3. At least one applicable requirement must be satisfiable from the images.

    Returns EvidenceCheckResult with met=True/False and a reason string.
    """
    if not _any_valid_image(image_results):
        return EvidenceCheckResult(
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "No usable images were submitted for this claim."
            ),
        )

    if not _any_matching_object(image_results, claim_object):
        return EvidenceCheckResult(
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                f"None of the valid images show a {claim_object}, "
                "so the evidence standard cannot be met."
            ),
        )

    applicable = [
        r for r in requirements
        if _requirement_applies(r, claim_object, issue_type)
    ]

    # Check whether any valid image has the claimed part visible
    valid_results = [r for r in image_results if r.valid_image]
    has_claimed_part = any(
        r.object_part != "unknown" for r in valid_results
    )

    if applicable and not has_claimed_part:
        req_text = applicable[0]["minimum_image_evidence"]
        return EvidenceCheckResult(
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                f"Evidence standard not met. Required: {req_text}"
            ),
        )

    # Multi-image: at least one must show claimed object clearly
    if len(image_results) > 1:
        return EvidenceCheckResult(
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "At least one image shows the claimed object and part clearly enough to evaluate."
            ),
        )

    return EvidenceCheckResult(
        evidence_standard_met=True,
        evidence_standard_met_reason=(
            "The submitted image shows the claimed object and part "
            "clearly enough to evaluate the claim."
        ),
    )