"""schemas.py — all Pydantic models for the pipeline."""

from __future__ import annotations
from pydantic import BaseModel, Field


class ConfidenceScore(BaseModel):
    """Internal confidence. Never written to output.csv."""
    object_confidence: float = Field(0.0, ge=0.0, le=1.0)
    damage_confidence: float = Field(0.0, ge=0.0, le=1.0)
    quality_penalty: float = Field(0.0, ge=0.0, le=1.0)

    @property
    def overall(self) -> float:
        base = (self.object_confidence * 0.4) + (self.damage_confidence * 0.6)
        return max(0.0, round(base - self.quality_penalty, 3))


class ImageAnalysisResult(BaseModel):
    """VLM result for one image."""
    image_id: str
    valid_image: bool = True
    detected_object: str = "unknown"
    matches_claim_object: bool = True
    object_part: str = "unknown"
    issue_type: str = "unknown"
    severity: str = "unknown"
    visual_description: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


class ClaimExtractionResult(BaseModel):
    """Text-only LLM result for claim parsing."""
    claimed_issue: str = "unknown"
    claimed_part: str = "unknown"
    claim_summary: str = ""
    claim_language: str = "english"
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class EvidenceCheckResult(BaseModel):
    """Python lookup result — no LLM."""
    evidence_standard_met: bool = False
    evidence_standard_met_reason: str = ""


class RiskAnalysisResult(BaseModel):
    """User history risk flags — no LLM."""
    risk_flags: list[str] = Field(default_factory=list)
    history_summary: str = ""


class DecisionResult(BaseModel):
    """Deterministic final decision."""
    claim_status: str = "not_enough_information"
    claim_status_justification: str = ""
    supporting_image_ids: list[str] = Field(default_factory=list)
    issue_type: str = "unknown"
    object_part: str = "unknown"
    severity: str = "unknown"
    valid_image: bool = True
    all_risk_flags: list[str] = Field(default_factory=list)


class OutputRow(BaseModel):
    """One row in output.csv — field order matches required columns."""
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    evidence_standard_met: str        # "true" or "false" string
    evidence_standard_met_reason: str
    risk_flags: str                   # semicolon-separated or "none"
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str         # semicolon-separated or "none"
    valid_image: str                  # "true" or "false" string
    severity: str