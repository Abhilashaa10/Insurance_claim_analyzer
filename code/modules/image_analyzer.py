"""image_analyzer.py — VLM call analyzing all images for a claim."""

import json
import re
from pathlib import Path

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE,
    RETRY_ATTEMPTS, RETRY_WAIT_SECONDS, RETRY_MAX_WAIT_SECONDS,
    IMAGE_RESPONSES_DIR,
)
from models.schemas import ImageAnalysisResult, ConfidenceScore
from utils.image_utils import load_images_for_api, get_image_id, parse_image_paths

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a damage assessment specialist for an insurance claim system.
You will receive one or more images submitted as evidence for a damage claim.
Analyze EACH image separately and return structured JSON only.

RULES:
- Base every field ONLY on what is visually present in the image.
- Do NOT infer damage from the user's claim text.
- Use "unknown" when you cannot determine a value with confidence.
- Use "none" for issue_type ONLY when the relevant part is clearly visible AND undamaged.
- If multiple damage types exist, select the most severe one.
- Return ONLY valid JSON. No prose, no markdown fences.

IMAGE QUALITY FLAGS (include all that apply):
blurry_image, cropped_or_obstructed, low_light_or_glare, wrong_angle,
wrong_object, wrong_object_part, damage_not_visible, claim_mismatch,
possible_manipulation, non_original_image, text_instruction_present

ALLOWED issue_type values:
dent, scratch, crack, glass_shatter, broken_part, missing_part,
torn_packaging, crushed_packaging, water_damage, stain, none, unknown

ALLOWED severity values: none, low, medium, high, unknown

Return a JSON object with this exact structure:
{
  "images": [
    {
      "image_id": "<filename without extension>",
      "valid_image": true,
      "detected_object": "<car|laptop|package|unknown>",
      "matches_claim_object": true,
      "object_part": "<part name as plain text>",
      "issue_type": "<one allowed value>",
      "severity": "<one allowed value>",
      "visual_description": "<one sentence of what you see>",
      "risk_flags": ["<flag1>", "<flag2>"],
      "confidence": {
        "object_confidence": 0.0,
        "damage_confidence": 0.0,
        "quality_penalty": 0.0
      }
    }
  ]
}"""


def _build_user_content(
    image_blocks: list[dict],
    image_ids: list[str],
    claim_object: str,
) -> list[dict]:
    """Build the user content array: images followed by instruction text."""
    content = list(image_blocks)
    ids_str = ", ".join(image_ids)
    content.append({
        "type": "text",
        "text": (
            f"Claim object type: {claim_object}\n"
            f"Image IDs in order: {ids_str}\n"
            f"Analyze each image separately and return the JSON structure described."
        ),
    })
    return content


def _parse_response(raw_text: str, image_ids: list[str]) -> list[ImageAnalysisResult]:
    """Parse VLM JSON response into ImageAnalysisResult list."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw_text).strip()
    data = json.loads(cleaned)
    results = []
    for i, img_data in enumerate(data.get("images", [])):
        image_id = img_data.get("image_id", image_ids[i] if i < len(image_ids) else f"img_{i+1}")
        conf_data = img_data.get("confidence", {})
        result = ImageAnalysisResult(
            image_id=image_id,
            valid_image=img_data.get("valid_image", True),
            detected_object=img_data.get("detected_object", "unknown"),
            matches_claim_object=img_data.get("matches_claim_object", True),
            object_part=img_data.get("object_part", "unknown"),
            issue_type=img_data.get("issue_type", "unknown"),
            severity=img_data.get("severity", "unknown"),
            visual_description=img_data.get("visual_description", ""),
            risk_flags=img_data.get("risk_flags", []),
            confidence=ConfidenceScore(
                object_confidence=float(conf_data.get("object_confidence", 0.5)),
                damage_confidence=float(conf_data.get("damage_confidence", 0.5)),
                quality_penalty=float(conf_data.get("quality_penalty", 0.0)),
            ),
        )
        results.append(result)
    return results


def _fallback_results(image_ids: list[str]) -> list[ImageAnalysisResult]:
    """Return safe fallback results when parsing fails."""
    return [
        ImageAnalysisResult(
            image_id=iid,
            valid_image=False,
            issue_type="unknown",
            severity="unknown",
            visual_description="Failed to parse model response.",
            risk_flags=["damage_not_visible"],
        )
        for iid in image_ids
    ]


def _save_raw_response(user_id: str, raw_text: str) -> None:
    """Save raw VLM response to logs/image_responses/."""
    log_path = IMAGE_RESPONSES_DIR / f"{user_id}.json"
    log_path.write_text(raw_text, encoding="utf-8")


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS),
)
def _call_vlm(content: list[dict]) -> str:
    """Call the VLM with retry logic."""
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def analyze_images(
    user_id: str,
    image_paths_str: str,
    claim_object: str,
    base_dir: Path,
) -> list[ImageAnalysisResult]:
    """Analyze all images for a claim in a single VLM call.

    Args:
        user_id:         For log file naming.
        image_paths_str: Semicolon-separated image paths from CSV.
        claim_object:    car | laptop | package.
        base_dir:        Project root for resolving image paths.

    Returns:
        One ImageAnalysisResult per image.
    """
    paths = parse_image_paths(image_paths_str)
    image_ids = [get_image_id(p) for p in paths]
    image_blocks = load_images_for_api(paths, base_dir)

    if not image_blocks:
        return _fallback_results(image_ids)

    content = _build_user_content(image_blocks, image_ids, claim_object)

    try:
        raw_text = _call_vlm(content)
        _save_raw_response(user_id, raw_text)
        return _parse_response(raw_text, image_ids)
    except json.JSONDecodeError:
        _save_raw_response(user_id, raw_text if 'raw_text' in dir() else "no response")
        return _fallback_results(image_ids)
    except Exception as e:
        print(f"[image_analyzer] ERROR for {user_id}: {e}")
        return _fallback_results(image_ids)