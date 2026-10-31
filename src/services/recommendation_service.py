"""Orchestrate the content-based book recommendation workflow."""

from __future__ import annotations

from typing import Any

from ..config import EMBEDDING_MODEL_NAME
from ..ml.embeddings import (
    SentenceTransformer,
    generate_embeddings,
)
from ..ml.preprocessing import prepare_profiles, validate_inputs
from ..ml.ranking import calculate_similarity, rank_books


def recommend_books(
    books: list[dict[str, Any]],
    user_preference: str,
    *,
    top_k: int | None = 3,
    model: SentenceTransformer | None = None,
    model_name: str = EMBEDDING_MODEL_NAME,
) -> list[dict[str, Any]]:
    """Run the content-based recommendation workflow."""

    # Validate
    preference = validate_inputs(user_preference, top_k)

    if not books:
        return []

    # Prepare semantic profiles
    valid_books, profiles = prepare_profiles(books)

    if not valid_books:
        return []

    # Initialize pretrained model
    embedding_model = (
        model if model is not None
        else SentenceTransformer(model_name)
    )

    # Generate user and book embeddings
    embeddings = generate_embeddings(
        [preference, *profiles],
        embedding_model,
    )

    # Calculate similarity
    scores = calculate_similarity(embeddings)

    # Rank recommendations
    return rank_books(valid_books, scores, top_k)


if __name__ == "__main__":
    # Run from the project root: python -m src.services.recommendation_service
    import json

    sample_books = [
        {
            "metadata": {
                "title": "Dune",
                "authors": ["Frank Herbert"],
                "subjects": ["Science fiction", "Politics", "Ecology"],
                "description": "A science fiction novel about power and survival on a desert planet.",
            }
        },
        {
            "metadata": {
                "title": "Deep Work",
                "authors": ["Cal Newport"],
                "subjects": ["Productivity", "Concentration"],
                "description": "Strategies for focused work and reducing distractions.",
            }
        },
    ]

    recommendations = recommend_books(
        books=sample_books,
        user_preference="I enjoy science fiction about distant planets and politics.",
        top_k=2,
    )
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
    