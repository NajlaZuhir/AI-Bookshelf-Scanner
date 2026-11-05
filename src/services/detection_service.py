"""Use OpenRouter first, then optional Google Vision OCR on failure."""

from pathlib import Path

from openai import APIError

from src.config import GOOGLE_VISION_FALLBACK_ENABLED
from src.integrations.google_vision_client import (
    GoogleVisionError,
    identify_book_candidates_with_google_vision,
)
from src.integrations.openrouter_client import identify_books_in_image


def detect_books(image_path: Path | str) -> dict:
    """Select a provider without treating valid empty detections as errors."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    print("Detection: using OpenRouter.", flush=True)

    try:
        result = identify_books_in_image(path)
    except (APIError, ValueError) as primary_error:
        if not GOOGLE_VISION_FALLBACK_ENABLED:
            raise

        print(
            "OpenRouter detection failed "
            f"({type(primary_error).__name__}). "
            "Trying Google Vision.",
            flush=True,
        )

        try:
            result = identify_book_candidates_with_google_vision(path)
        except GoogleVisionError as fallback_error:
            raise RuntimeError(
                "Book detection failed with both OpenRouter and Google Vision. "
                f"{fallback_error}"
            ) from fallback_error

        return {**result, "detection_source": "google_vision"}

    return {**result, "detection_source": "openrouter"}
