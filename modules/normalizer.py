"""normalizer.py — convert free-text model outputs to allowed enum values."""

from models.schemas import ImageAnalysisResult, ClaimExtractionResult
from utils.enum_mapper import map_issue_type, map_object_part, map_severity
from config import ALLOWED_RISK_FLAGS, ALLOWED_OBJECT_PARTS


def _clean_risk_flags(flags: list[str]) -> list[str]:
    """Keep only allowed risk flag values."""
    return [f for f in flags if f in ALLOWED_RISK_FLAGS]


def _normalize_object_part(raw_part: str, claim_object: str) -> str:
    """Try direct lookup first, then enum_mapper."""
    allowed = ALLOWED_OBJECT_PARTS.get(claim_object, set())
    if raw_part in allowed:
        return raw_part
    return map_object_part(raw_part, claim_object)


def normalize_image_result(
    result: ImageAnalysisResult,
    claim_object: str,
) -> ImageAnalysisResult:
    """Normalize all enum fields on an ImageAnalysisResult in place.

    Returns the same object with corrected field values.
    """
    result.issue_type = (
        result.issue_type
        if result.issue_type in {"dent","scratch","crack","glass_shatter",
                                  "broken_part","missing_part","torn_packaging",
                                  "crushed_packaging","water_damage","stain",
                                  "none","unknown"}
        else map_issue_type(result.issue_type)
    )
    result.object_part = _normalize_object_part(result.object_part, claim_object)
    result.severity = (
        result.severity
        if result.severity in {"none","low","medium","high","unknown"}
        else map_severity(result.severity)
    )
    result.risk_flags = _clean_risk_flags(result.risk_flags)
    return result


def normalize_claim_result(
    result: ClaimExtractionResult,
    claim_object: str,
) -> ClaimExtractionResult:
    """Normalize claimed_issue and claimed_part on a ClaimExtractionResult."""
    result.claimed_issue = map_issue_type(result.claimed_issue)
    result.claimed_part = _normalize_object_part(result.claimed_part, claim_object)
    return result