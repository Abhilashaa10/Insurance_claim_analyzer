from __future__ import annotations
from pydantic import BaseModel, Field


# ── Internal confidence (not in output.csv) ───────────────────────────────────

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
    """Result for a single image from the VLM call."""
    image_id: str                              # e.g. "img_1"
    valid_image: bool = True
    detected_object: str = "unknown"           # car | laptop | package | unknown
    object_part: str = "unknown"
    issue_type: str = "unknown"
    severity: str = "unknown"
    visual_description: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)


# ── Stage 2: claim extraction result ─────────────────────────────────────────

class ClaimExtractionResult(BaseModel):
    """Structured output from the claim extractor LLM call."""
    claimed_issue: str = "unknown"             # normalized issue type
    claimed_part: str = "unknown"              # normalized object part
    claim_summary: str = ""                    # one-line plain English summary
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
    """Final deterministic decision for a claim."""
    claim_status: str = "not_enough_information"
    claim_status_justification: str = ""
    supporting_image_ids: list[str] = Field(default_factory=list)
    issue_type: str = "unknown"
    object_part: str = "unknown"
    severity: str = "unknown"


# ── Final output row (maps 1:1 to output.csv columns) ────────────────────────

class OutputRow(BaseModel):
    """One row written to output.csv. Field order matches required columns."""
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    evidence_standard_met: bool
    evidence_standard_met_reason: str
    risk_flags: str                            # semicolon-separated or "none"
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str                  # semicolon-separated or "none"
    valid_image: bool
    severity: str