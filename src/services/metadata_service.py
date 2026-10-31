"""Detect books, retrieve their metadata, and summarize lookup results."""

import sys
from pathlib import Path
import json
from typing import Any


if __package__:
    from ..integrations.open_library_client import find_all_books
    from ..integrations.openrouter_client import identify_books_in_image
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.integrations.open_library_client import find_all_books
    from src.integrations.openrouter_client import identify_books_in_image


def scan_books(image_path: Path | str) -> dict[str, Any]:
    """Return detected books enriched with metadata and lookup status counts."""
    vlm_results = identify_books_in_image(image_path)
    book_results = find_all_books(vlm_results.get("books", []))

    return {
        "total_detected": len(book_results),
        "total_matched": sum(
            b["match_status"] == "matched"
            for b in book_results
        ),
        "total_unmatched": sum(
            b["match_status"] == "unmatched"
            for b in book_results
        ),
        "total_api_errors": sum(
            b["match_status"] == "api_error"
            for b in book_results
        ),
        "books": book_results
    }

# usage example
if __name__ == "__main__":
    image_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "book_1.jpg"
    )

    output_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "books_metadata.json"
    )

    results = scan_books(image_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved metadata to {output_path}")
    print(json.dumps(results, indent=2, ensure_ascii=False))
