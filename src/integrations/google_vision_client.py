"""Extract candidate book titles from Google Vision OCR paragraphs."""

from functools import lru_cache
from pathlib import Path

from src.integrations.detection_schemas import BookDetectionResult


class GoogleVisionError(RuntimeError):
    """Google Vision could not complete recognition."""


@lru_cache(maxsize=1)
def get_google_vision_client():
    """Initialize the optional SDK and its credentials only when needed."""
    from google.cloud import vision

    return vision.ImageAnnotatorClient()


def identify_book_candidates_with_google_vision(
    image_path: Path | str,
) -> dict:
    """Return OCR candidates; Open Library matching happens downstream."""
    try:
        from google.cloud import vision
        from google.api_core.exceptions import GoogleAPIError
        from google.auth.exceptions import GoogleAuthError
    except ImportError as exc:
        raise GoogleVisionError(
            "Install google-cloud-vision to enable the fallback."
        ) from exc

    # File access errors are local failures, rather than provider failures.
    image_bytes = Path(image_path).read_bytes()

    try:
        response = get_google_vision_client().document_text_detection(
            image=vision.Image(content=image_bytes),
            timeout=30,
            retry=None,
        )
    except (GoogleAPIError, GoogleAuthError) as exc:
        raise GoogleVisionError(
            "Google Vision authentication or API request failed."
        ) from exc

    if response.error.message:
        raise GoogleVisionError(response.error.message)

    candidates = []
    seen = set()

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                words = [
                    "".join(symbol.text for symbol in word.symbols)
                    for word in paragraph.words
                ]
                text = " ".join(" ".join(words).split())
                key = text.casefold()

                if not text or not any(char.isalpha() for char in text):
                    continue
                if key in seen:
                    continue

                seen.add(key)
                candidates.append({
                    "book_number": len(candidates) + 1,
                    "title": text,
                    "author": None,
                })

    result = BookDetectionResult.model_validate(
        {"books": candidates},
        strict=True,
    )

    print(
        f"Google Vision returned {len(candidates)} candidate titles.",
        flush=True,
    )
    return result.model_dump()
