"""schemas.py — all Pydantic models for the pipeline."""

from __future__ import annotations
from pydantic import BaseModel, Field


# ── Input models ──────────────────────────────────────────────────────────────

class ClaimInput(BaseModel):
    """One row from claims.csv or sample_claims.csv."""
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str


class UserHistory(BaseModel):
    """One row from user_history.csv."""
    user_id: str
    past_claim_count: int = 0
    accept_claim: int = 0
    manual_review_claim: int = 0
    rejected_claim: int = 0
    last_90_days_claim_count: int = 0
    history_flags: str = "none"
    history_summary: str = ""


# ── Internal confidence (never written to output.csv) ─────────────────────────

class ConfidenceScore(BaseModel):
    """Internal confidence tracking. Drives decision engine routing."""
    object_confidence: float = Field(0.0, ge=0.0, le=1.0)
    damage_confidence: float = Field(0.0, ge=0.0, le=1.0)
    quality_penalty: float = Field(0.0, ge=0.0, le=1.0)

    @property
    def overall(self) -> float:
        base = (self.object_confidence * 0.4) + (self.damage_confidence * 0.6)
        return max(0.0, round(base - self.quality_penalty, 3))


# ── Stage 1: per-image result from image_analyzer ────────────────────────────

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
    processing_notes: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


# ── Stage 2: claim extraction result ─────────────────────────────────────────

class ClaimExtractionResult(BaseModel):
    """Text-only LLM result for claim parsing."""
    claimed_issue: str = "unknown"
    claimed_part: str = "unknown"
    claim_summary: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)


# ── Stage 3: evidence checker result ─────────────────────────────────────────

class EvidenceCheckResult(BaseModel):
    """Output of the Python evidence requirements lookup."""
    evidence_standard_met: bool = False
    evidence_standard_met_reason: str = ""


# ── Stage 4: risk analyzer result ────────────────────────────────────────────

class RiskAnalysisResult(BaseModel):
    """Output of the Python user history risk check."""
    risk_flags: list[str] = Field(default_factory=list)
    history_summary: str = ""


# ── Stage 5: decision engine result ──────────────────────────────────────────

class DecisionResult(BaseModel):
    """Deterministic final decision."""
    claim_status: str = "not_enough_information"
    claim_status_justification: str = ""
    supporting_image_ids: list[str] = Field(default_factory=list)
    issue_type: str = "unknown"
    object_part: str = "unknown"
    severity: str = "unknown"
    valid_image: bool = True
    risk_flags: list[str] = Field(default_factory=list)


# ── Final output row (maps 1:1 to output.csv columns) ────────────────────────

class OutputRow(BaseModel):
    """One row written to output.csv. Booleans serialized as lowercase strings."""
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    evidence_standard_met: str        # "true" or "false" — converted at write time
    evidence_standard_met_reason: str
    risk_flags: str                   # semicolon-separated or "none"
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str         # semicolon-separated or "none"
    valid_image: str                  # "true" or "false" — converted at write time
    severity: str