"""Detect, enrich, save, and rank the books in a bookshelf image.
python -m src.cli
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import EMBEDDING_MODEL_NAME
from src.database.repositories.book_repository import BookRepository
from src.database.repositories.recommendation_repository import RecommendationResultRepository
from src.database.repositories.scan_repository import ScanRepository
from src.ml.preprocessing import validate_inputs
from src.services.metadata_service import scan_books
from src.services.recommendation_service import recommend_books


scan_repo = ScanRepository()
book_repo = BookRepository()
recommendation_repo = RecommendationResultRepository()


def process_bookshelf(
    image_path: Path | str,
    user_preference: str,
    top_k: int | None = 3,
) -> list[dict[str, Any]]:
    """Save matched books and recommendations with their database book IDs."""
    preference = validate_inputs(user_preference, top_k)

    # 1-2. Detect books and retrieve metadata.
    scan_results = scan_books(image_path)
    books_with_metadata = scan_results["books"]

    # 3. Save detected books to PostgreSQL
    scan_id = scan_repo.create(str(image_path))
    for book in books_with_metadata:
        if book["match_status"] == "matched":
            book_repo.create(scan_id, book)

    # Database records include the book_id retained by the ranking module.
    scanned_books = book_repo.get_by_scan(scan_id)

    # 4. Generate personalized recommendations
    selected_books = recommend_books(
        scanned_books,
        preference,
        top_k=top_k,
        model_name=EMBEDDING_MODEL_NAME,
    )

    # 5. Save recommendation results to PostgreSQL
    recommendation_repo.create(
        scan_id=scan_id,
        model_name=EMBEDDING_MODEL_NAME,
        preference_text=preference,
        top_k=top_k,
        ranked_outcome=selected_books,
    )

    # 6. Return ranked books
    return selected_books
