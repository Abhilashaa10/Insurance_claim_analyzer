import base64
from pathlib import Path


def get_image_id(image_path: str) -> str:
    """Return filename without extension as the image ID.

    Example: 'images/test/case_001/img_1.jpg' → 'img_1'
    """
    return Path(image_path).stem


def encode_image_to_base64(image_path: str, base_dir: Path) -> str:
    """Read an image file and return its base64-encoded string.

    Args:
        image_path: Relative path as stored in the CSV.
        base_dir:   Project root so we can resolve the full path.

    Raises:
        FileNotFoundError: If the image does not exist on disk.
    """
    full_path = base_dir / image_path
    if not full_path.exists():
        raise FileNotFoundError(f"Image not found: {full_path}")
    with open(full_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: str) -> str:
    """Infer MIME type from file extension.

    Defaults to image/jpeg for unknown extensions.
    """
    suffix = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return media_types.get(suffix, "image/jpeg")


def parse_image_paths(image_paths_str: str) -> list[str]:
    """Split semicolon-separated image paths into a list.

    Example:
        'images/test/case_001/img_1.jpg;images/test/case_001/img_2.jpg'
        → ['images/test/case_001/img_1.jpg', 'images/test/case_001/img_2.jpg']
    """
    return [p.strip() for p in image_paths_str.split(";") if p.strip()]


def load_images_for_api(
    image_paths: list[str],
    base_dir: Path,
) -> list[dict]:
    """Build the image content blocks for the Anthropic API.

    Returns a list of dicts ready to be inserted into the `content` array.
    Skips images that cannot be found and logs a warning.
    """
    blocks = []
    for path in image_paths:
        try:
            data = encode_image_to_base64(path, base_dir)
            media_type = get_image_media_type(path)
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": data,
                },
            })
        except FileNotFoundError as e:
            print(f"[image_utils] WARNING: {e} — skipping.")
    return blocks