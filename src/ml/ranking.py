"""Score and rank books using normalized semantic embeddings."""

from __future__ import annotations

from typing import Any

import numpy as np


def calculate_similarity(
    embeddings: np.ndarray,
) -> np.ndarray:
    """Compare each book embedding with the user embedding."""

    user_embedding = embeddings[0]
    book_embeddings = embeddings[1:]

    return book_embeddings @ user_embedding


def rank_books(
    books: list[dict[str, Any]],
    scores: np.ndarray,
    top_k: int | None,
) -> list[dict[str, Any]]:
    """Sort books by similarity and return the top results."""

    ranked = []

    for book, score in zip(books, scores):
        metadata = book["metadata"]

        result = {
            "title": metadata.get("title"),
            "authors": metadata.get("authors"),
            "similarity": round(float(score), 6),
            "work_id": metadata.get("work_id"),
        }
        if "book_id" in book:
            result["book_id"] = book["book_id"]
        ranked.append(result)

    ranked.sort(
        key=lambda book: book["similarity"],
        reverse=True,
    )

    return ranked[:top_k] if top_k is not None else ranked
