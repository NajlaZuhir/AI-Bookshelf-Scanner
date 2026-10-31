
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from src.database.connection import get_connection
else:
    from ..connection import get_connection


class BookRepository:

    def create(self, scan_id: int, book: dict) -> int:
        """Save a book containing a nested Open Library metadata dictionary."""
        metadata = book.get("metadata")
        if not isinstance(metadata, dict) or not metadata:
            raise ValueError("book must contain a non-empty metadata dictionary")

        query = """
                    INSERT INTO books (
                        scan_id,
                        work_id,
                        title,
                        authors,
                        description,
                        subjects
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING book_id;
        """
        params = (
            scan_id,
            metadata.get("work_id"),
            metadata.get("title"),
            metadata.get("authors") or [],
            metadata.get("description"),
            metadata.get("subjects") or [],
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()[0]


    def get_by_id(self, book_id: int) -> dict | None:
        """Retrieve a book by its ID."""

        query = """
            SELECT
                book_id, work_id, title, authors,
                description, subjects
            FROM books
            WHERE book_id = %s
            ORDER BY book_id;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (book_id,))
                row = cur.fetchone()
                return self._to_book(row) if row else None


    def get_all(self) -> list[dict]:
        """Retrieve all books."""
        query = """
            SELECT
                book_id, work_id, title, authors,
                description, subjects
            FROM books
            ORDER BY book_id;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [self._to_book(row) for row in cur.fetchall()]


    def get_by_scan(self, scan_id: int) -> list[dict]:
        """Retrieve all books belonging to a scan."""
        query = """
            SELECT
                book_id, work_id, title, authors,
                description, subjects
            FROM books
            WHERE scan_id = %s
            ORDER BY book_id;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (scan_id,))
                return [self._to_book(row) for row in cur.fetchall()]
                    
    @staticmethod
    def _to_book(row: tuple) -> dict:
        """Convert a database row to a book dictionary."""
        return {
            "book_id": row[0],
            "metadata": {
                "work_id": row[1],
                "title": row[2],
                "authors": row[3],
                "description": row[4],
                "subjects": row[5],
            },
        }

