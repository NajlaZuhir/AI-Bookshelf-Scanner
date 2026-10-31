"""Load and prepare book metadata for semantic recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_METADATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "books_metadata.json"
)


def load_books(
    metadata_path: Path | str = DEFAULT_METADATA_PATH,
) -> list[dict[str, Any]]:
    """Load books successfully matched with Open Library."""

    path = Path(metadata_path)

    with path.open(encoding="utf-8") as metadata_file:
        data = json.load(metadata_file)

    books = data.get("books", [])

    if not isinstance(books, list):
        raise ValueError(f"Expected 'books' to be a list in {path}")

    return [
        book
        for book in books
        if isinstance(book, dict)
        and book.get("match_status") == "matched"
        and isinstance(book.get("metadata"), dict)
    ]


def _as_text(value: Any) -> str:
    """Convert strings and collections into clean text."""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, Iterable) and not isinstance(
        value, (bytes, dict)
    ):
        return ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return ""


def book_profile(book: dict[str, Any]) -> str:
    """Represent book content using subjects and description."""

    metadata = book.get("metadata") or {}

    title = _as_text(metadata.get("title"))
    description = _as_text(metadata.get("description"))
    subjects = _as_text(metadata.get("subjects"))

    if description:
        if subjects:
            return f"Subjects: {subjects}\nDescription: {description}"

        return f"Description: {description}"

    if subjects:
        return f"Subjects: {subjects}"

    return f"Title: {title}" if title else ""


def validate_inputs(
    user_preference: str,
    top_k: int | None,
) -> str:
    """Validate and normalize recommendation parameters."""

    preference = user_preference.strip()

    if not preference:
        raise ValueError("user_preference must not be empty")

    if top_k is not None and (type(top_k) is not int or top_k < 1):
        raise ValueError("top_k must be an integer of at least 1")

    return preference


def prepare_profiles(
    books: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Prepare semantic profiles for books with usable metadata."""

    valid_books = []
    profiles = []

    for book in books:
        profile = book_profile(book)

        if not profile:
            continue

        valid_books.append(book)
        profiles.append(profile)

    return valid_books, profiles
