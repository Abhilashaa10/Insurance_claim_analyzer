"""claim_extractor.py — text-only LLM to extract structured claim from conversation."""

import json
import re

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE,
    RETRY_ATTEMPTS, RETRY_WAIT_SECONDS, RETRY_MAX_WAIT_SECONDS,
    CLAIM_RESPONSES_DIR,
)
from models.schemas import ClaimExtractionResult

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a claim parsing assistant for an insurance system.
You will receive a customer support conversation and the type of object being claimed.
Extract the structured claim information and return JSON only.

RULES:
- Read only what the customer actually says. Do not invent details.
- The conversation may be in English, Hindi, Urdu, or mixed language. Handle all.
- Use "unknown" when a field cannot be determined from the conversation.
- Return ONLY valid JSON. No prose, no markdown fences.

Return this exact JSON structure:
{
  "claimed_issue": "<damage type in plain text, e.g. dent, scratch, crack>",
  "claimed_part": "<object part in plain text, e.g. rear bumper, screen, package corner>",
  "claim_summary": "<one sentence describing what the customer is claiming>",
  "claim_language": "<english|hindi|mixed|other>",
  "confidence": 0.0
}"""


def _save_raw_response(user_id: str, raw_text: str) -> None:
    log_path = CLAIM_RESPONSES_DIR / f"{user_id}.json"
    log_path.write_text(raw_text, encoding="utf-8")


def _parse_response(raw_text: str) -> ClaimExtractionResult:
    cleaned = re.sub(r"```(?:json)?|```", "", raw_text).strip()
    data = json.loads(cleaned)
    return ClaimExtractionResult(
        claimed_issue=data.get("claimed_issue", "unknown"),
        claimed_part=data.get("claimed_part", "unknown"),
        claim_summary=data.get("claim_summary", ""),
        claim_language=data.get("claim_language", "english"),
        confidence=float(data.get("confidence", 0.5)),
    )


def _fallback() -> ClaimExtractionResult:
    return ClaimExtractionResult(
        claimed_issue="unknown",
        claimed_part="unknown",
        claim_summary="Could not extract claim from conversation.",
        confidence=0.0,
    )


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS),
)
def _call_llm(user_claim: str, claim_object: str) -> str:
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=512,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Claim object type: {claim_object}\n\n"
                f"Conversation:\n{user_claim}"
            ),
        }],
    )
    return response.content[0].text


def extract_claim(
    user_id: str,
    user_claim: str,
    claim_object: str,
) -> ClaimExtractionResult:
    """Extract structured claim from a support conversation.

    Args:
        user_id:      For log file naming.
        user_claim:   Raw conversation text from CSV.
        claim_object: car | laptop | package.

    Returns:
        ClaimExtractionResult with claimed issue, part, and summary.
    """
    try:
        raw_text = _call_llm(user_claim, claim_object)
        _save_raw_response(user_id, raw_text)
        return _parse_response(raw_text)
    except json.JSONDecodeError:
        _save_raw_response(user_id, raw_text if 'raw_text' in dir() else "no response")
        return _fallback()
    except Exception as e:
        print(f"[claim_extractor] ERROR for {user_id}: {e}")
        return _fallback()