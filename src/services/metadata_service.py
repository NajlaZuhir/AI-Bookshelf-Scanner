"""Detect books, retrieve their metadata, and summarize lookup results."""

import sys
from pathlib import Path
import json
from typing import Any
import logging
from psycopg import Error as DatabaseError


if __package__:
    from ..database.repositories.book_metadata_cache_repository import (
        BookMetadataCacheRepository,
    )
    from ..integrations.open_library_client import (
        find_all_books,
        run_find_book,
    )
    from .detection_service import detect_books
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from src.database.repositories.book_metadata_cache_repository import (
        BookMetadataCacheRepository,
    )
    from src.integrations.open_library_client import (
        find_all_books,
        run_find_book,
    )
    from src.services.detection_service import detect_books


logger = logging.getLogger(__name__)
metadata_cache = BookMetadataCacheRepository()


def normalize_cache_key(value: str | None) -> str:
    """Ignore capitalization and repeated whitespace."""
    return " ".join((value or "").casefold().split())


def find_book_with_cache(
    title: str,
    author: str | None = None,
) -> dict | None:
    title_key = normalize_cache_key(title)
    author_key = normalize_cache_key(author)

    if not title_key:
        return None

    # 1. Try a fresh cache entry.
    cache_status = "Cache miss"
    try:
        cached_metadata = metadata_cache.get(
            title_key,
            author_key,
        )
    except DatabaseError as exc:
        logger.warning("Metadata cache read failed: %s", exc)
        cached_metadata = None
        cache_status = "Cache unavailable"

    if cached_metadata is not None:
        print(f"Cache hit: {title} - using stored metadata", flush=True)
        return cached_metadata

    # 2. Perform the existing Open Library lookup.
    # Request errors still reach find_all_books(), which handles them.
    print(f"{cache_status}: {title} - fetching from Open Library", flush=True)
    metadata = run_find_book(title, author)

    # 3. Cache successful matches only.
    if metadata:
        try:
            metadata_cache.save(
                title_key,
                author_key,
                metadata,
            )
        except DatabaseError as exc:
            logger.warning("Metadata cache write failed: %s", exc)
        else:
            print(f"Cache saved: {title}", flush=True)
    else:
        print(f"Cache skipped: {title} - no metadata match", flush=True)

    return metadata


def scan_books(image_path: Path | str) -> dict[str, Any]:
    """Return detected books enriched with metadata and lookup status counts."""
    detection_results = detect_books(image_path)
    book_results = find_all_books(
        detection_results.get("books", []),
        find_book=find_book_with_cache,
    )

    if detection_results["detection_source"] == "google_vision":
        # Different OCR fragments can match the same work. Keep one match.
        unique_results = []
        seen_work_ids = set()
        for book in book_results:
            metadata = book.get("metadata") or {}
            work_id = metadata.get("work_id")
            if book["match_status"] == "matched" and work_id:
                if work_id in seen_work_ids:
                    continue
                seen_work_ids.add(work_id)
            unique_results.append(book)
        book_results = unique_results

    return {
        "detection_source": detection_results["detection_source"],
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
