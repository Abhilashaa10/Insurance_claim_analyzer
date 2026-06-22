"""debug_test.py — run this at project root to find the exact failure point."""

import sys
import json
import base64
from pathlib import Path

# ── Step 1: Check config loads ────────────────────────────────────────────────
print("=" * 50)
print("STEP 1: Config")
try:
    from config import (
        ANTHROPIC_API_KEY, MODEL_NAME, BASE_DIR, DATASET_DIR,
        IMAGE_RESPONSES_DIR, CLAIM_RESPONSES_DIR
    )
    print(f"  BASE_DIR     : {BASE_DIR}")
    print(f"  DATASET_DIR  : {DATASET_DIR}")
    print(f"  MODEL_NAME   : {MODEL_NAME}")
    print(f"  API_KEY set  : {'YES' if ANTHROPIC_API_KEY else 'NO - THIS IS THE BUG'}")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

# ── Step 2: Check image file exists ───────────────────────────────────────────
print("\nSTEP 2: Image file existence")
test_path = DATASET_DIR / "images" / "test" / "case_001" / "img_1.jpg"
print(f"  Looking for  : {test_path}")
print(f"  Exists       : {test_path.exists()}")

# Also scan what actually exists
img_root = DATASET_DIR / "images"
if img_root.exists():
    all_imgs = list(img_root.rglob("*.jpg")) + list(img_root.rglob("*.png"))
    print(f"  Total images found under dataset/images/: {len(all_imgs)}")
    if all_imgs:
        print(f"  First found  : {all_imgs[0]}")
else:
    print(f"  dataset/images/ does NOT exist at {img_root}")

# ── Step 3: Check base64 encoding ────────────────────────────────────────────
print("\nSTEP 3: Base64 encode")
if test_path.exists():
    with open(test_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    print(f"  Encoded OK, length: {len(data)} chars")
else:
    print("  SKIPPED - file not found")

# ── Step 4: Check anthropic client ───────────────────────────────────────────
print("\nSTEP 4: Anthropic client")
try:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    print(f"  Client created OK, model={MODEL_NAME}")
except Exception as e:
    print(f"  FAILED: {e}")

# ── Step 5: Send ONE real image to Claude ─────────────────────────────────────
print("\nSTEP 5: Real API call with one image")
if test_path.exists() and ANTHROPIC_API_KEY:
    try:
        with open(test_path, "rb") as f:
            img_data = base64.standard_b64encode(f.read()).decode("utf-8")

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_data,
                        },
                    },
                    {"type": "text", "text": "What object is in this image? Reply in one sentence."}
                ]
            }]
        )
        print(f"  API response: {response.content[0].text}")
    except Exception as e:
        print(f"  API CALL FAILED: {e}")
else:
    print("  SKIPPED - no image or no API key")

# ── Step 6: Check image_utils parse_image_paths ───────────────────────────────
print("\nSTEP 6: parse_image_paths")
try:
    from utils.image_utils import parse_image_paths, load_images_for_api
    sample_paths = "images/test/case_001/img_1.jpg;images/test/case_001/img_2.jpg"
    parsed = parse_image_paths(sample_paths)
    print(f"  Parsed paths : {parsed}")
    blocks = load_images_for_api(parsed, DATASET_DIR)
    print(f"  Image blocks : {len(blocks)} loaded")
    if not blocks:
        print("  BUG: load_images_for_api returned empty list")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "=" * 50)
print("DEBUG COMPLETE")