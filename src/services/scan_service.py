"""Detect books, retrieve metadata, and save a scan."""

from pathlib import Path

from src.database.connection import get_connection
from src.database.repositories.scan_repository import ScanRepository
from src.database.repositories.book_repository import BookRepository
from src.services.metadata_service import scan_books


scan_repository = ScanRepository()
book_repository = BookRepository()


def process_scan(image_path: Path | str) -> dict:
    results = scan_books(image_path)

    # Save the scan and matched books together.
    with get_connection() as connection:
        scan_id = scan_repository.create(
            str(image_path),
            connection=connection,
        )

        for book in results["books"]:
            if book["match_status"] == "matched":
                book["book_id"] = book_repository.create(
                    scan_id,
                    book,
                    connection=connection,
                )

    return {
        "scan_id": scan_id,
        **results,
    }