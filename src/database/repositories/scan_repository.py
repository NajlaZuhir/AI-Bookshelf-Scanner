

from pathlib import Path
from contextlib import nullcontext

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from src.database.connection import get_connection
else:
    from ..connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _storage_image_path(image_path: str | Path) -> str:
    """Return project-relative paths for images stored in this project."""
    path = Path(image_path)
    if path.is_absolute():
        try:
            path = path.relative_to(PROJECT_ROOT)
        except ValueError:
            pass
    return str(path)


class ScanRepository:

    def create(self, image_path: str, *, connection=None) -> int:
        """Store a new bookshelf scan and return its ID."""

        query ="""
            INSERT INTO scan (image_path)
            VALUES (%s)
            RETURNING scan_id;
        """
        with (
        nullcontext(connection)
            if connection is not None
            else get_connection()
        ) as conn:    
            with conn.cursor() as cur:
                cur.execute(query,(_storage_image_path(image_path),))
                return cur.fetchone()[0]

    def get_by_id(self, scan_id: int) -> dict | None:
        """Retrieve a scan by its ID."""

        query = """
            SELECT scan_id, image_path, created_at
            FROM scan
            WHERE scan_id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (scan_id,))
                row = cur.fetchone()

                if row is None:
                    return None

                return {
                    "scan_id": row[0],
                    "image_path": row[1],
                    "created_at": row[2],
                }

    def get_all(self) -> list[dict]:
        """Retrieve all scans."""

        query = """
            SELECT scan_id, image_path, created_at
            FROM scan
            ORDER BY created_at DESC;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                return [
                    {
                        "scan_id": row[0],
                        "image_path": row[1],
                        "created_at": row[2],
                    }
                    for row in rows
                ]


