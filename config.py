import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API ──────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "claude-sonnet-4-6")

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).parent
DATASET_DIR: Path = BASE_DIR / "dataset"
LOGS_DIR: Path = BASE_DIR / "logs"
IMAGE_RESPONSES_DIR: Path = LOGS_DIR / "image_responses"
CLAIM_RESPONSES_DIR: Path = LOGS_DIR / "claim_responses"

# ── Dataset files ─────────────────────────────────────────────────────────────
CLAIMS_CSV: Path = DATASET_DIR / "claims.csv"
SAMPLE_CLAIMS_CSV: Path = DATASET_DIR / "sample_claims.csv"
USER_HISTORY_CSV: Path = DATASET_DIR / "user_history.csv"
EVIDENCE_REQUIREMENTS_CSV: Path = DATASET_DIR / "evidence_requirements.csv"

# ── Output ───────────────────────────────────────────────────────────────────
OUTPUT_CSV: Path = BASE_DIR / "output.csv"

# ── LLM settings ─────────────────────────────────────────────────────────────
MAX_TOKENS: int = 2048
TEMPERATURE: float = 0.0   # deterministic outputs

# ── Retry settings (tenacity) ─────────────────────────────────────────────────
RETRY_ATTEMPTS: int = 3
RETRY_WAIT_SECONDS: int = 5
RETRY_MAX_WAIT_SECONDS: int = 30

# ── Confidence thresholds ─────────────────────────────────────────────────────
# Below this → decision engine falls back to not_enough_information
CONFIDENCE_THRESHOLD: float = 0.45

# ── Allowed output values ─────────────────────────────────────────────────────
ALLOWED_CLAIM_STATUS = {"supported", "contradicted", "not_enough_information"}

ALLOWED_ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part",
    "missing_part", "torn_packaging", "crushed_packaging",
    "water_damage", "stain", "none", "unknown",
}

ALLOWED_SEVERITY = {"none", "low", "medium", "high", "unknown"}

ALLOWED_RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required",
}

CAR_PARTS = {
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender",
    "quarter_panel", "body", "unknown",
}

LAPTOP_PARTS = {
    "screen", "keyboard", "trackpad", "hinge", "lid",
    "corner", "port", "base", "body", "unknown",
}

PACKAGE_PARTS = {
    "box", "package_corner", "package_side", "seal",
    "label", "contents", "item", "unknown",
}

ALLOWED_OBJECT_PARTS: dict[str, set[str]] = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS,
}

# ── Ensure log dirs exist ─────────────────────────────────────────────────────
IMAGE_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
CLAIM_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)