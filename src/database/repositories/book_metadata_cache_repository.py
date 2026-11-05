"""Store and retrieve shared Open Library metadata."""

from psycopg.types.json import Jsonb

from ..connection import get_connection


class BookMetadataCacheRepository:

    def get(
        self,
        lookup_title: str,
        lookup_author: str,
    ) -> dict | None:
        """Return metadata only while its cache entry is fresh."""
        query = """
            SELECT metadata
            FROM book_metadata_cache
            WHERE lookup_title = %s
              AND lookup_author = %s
              AND expires_at > CURRENT_TIMESTAMP;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (lookup_title, lookup_author))
                row = cur.fetchone()
                return row[0] if row else None

    def save(
        self,
        lookup_title: str,
        lookup_author: str,
        metadata: dict,
    ) -> None:
        """Create or refresh an entry for 30 days."""
        query = """
            INSERT INTO book_metadata_cache (
                lookup_title,
                lookup_author,
                metadata,
                cached_at,
                expires_at
            )
            VALUES (
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP + INTERVAL '30 days'
            )
            ON CONFLICT (lookup_title, lookup_author)
            DO UPDATE SET
                metadata = EXCLUDED.metadata,
                cached_at = EXCLUDED.cached_at,
                expires_at = EXCLUDED.expires_at;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        lookup_title,
                        lookup_author,
                        Jsonb(metadata),
                    ),
                )