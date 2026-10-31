
from psycopg.types.json import Jsonb
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from src.database.connection import get_connection
else:
    from ..connection import get_connection

class RecommendationResultRepository:

    def create(
        self,
        scan_id: int,
        model_name: str,
        preference_text: str,
        top_k: int | None,
        ranked_outcome: list[dict],
    ) -> int:
        """Save a result; top_k=None stores the number of returned books (possibly 0)."""
        if top_k is not None and (type(top_k) is not int or top_k < 1):
            raise ValueError("top_k must be a positive integer or None")
        if not isinstance(ranked_outcome, list):
            raise TypeError("ranked_outcome must be a list")

        stored_top_k = len(ranked_outcome) if top_k is None else top_k

        query = """
            INSERT INTO recommendation_result (
                scan_id,
                model_name,
                preference_text,
                top_k,
                ranked_outcome
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING result_id;
        """
        params = (
            scan_id,
            model_name,
            preference_text,
            stored_top_k,
            Jsonb(ranked_outcome),
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()[0]



    def get_by_id(self, result_id: int) -> dict | None:
        """Retrieve one recommendation result by its ID."""

        query = """
            SELECT
                result_id, scan_id, model_name, preference_text,
                top_k, ranked_outcome, created_at
            FROM recommendation_result
            WHERE result_id = %s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (result_id,))
                row = cur.fetchone()
                return self._to_result(row) if row else None
            

    def get_all(self) -> list[dict]:
        """Retrieve all recommendation results, newest first."""

        query = """
            SELECT
                result_id, scan_id, model_name, preference_text,
                top_k, ranked_outcome, created_at
            FROM recommendation_result
            ORDER BY created_at DESC, result_id DESC;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [self._to_result(row) for row in cur.fetchall()]

    
    def get_by_scan_id(self, scan_id: int) -> list[dict]:
            """Retrieve recommendation history for a scan, newest first."""
    
            query = """
                SELECT
                    result_id, scan_id, model_name, preference_text,
                    top_k, ranked_outcome, created_at
                FROM recommendation_result
                WHERE scan_id = %s
                ORDER BY created_at DESC, result_id DESC;
            """
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (scan_id,))
                    return [self._to_result(row) for row in cur.fetchall()]
                
    @staticmethod
    def _to_result(row: tuple) -> dict:
        return {
            "result_id": row[0],
            "scan_id": row[1],
            "model_name": row[2],
            "preference_text": row[3],
            "top_k": row[4],
            "ranked_outcome": row[5],
            "created_at": row[6],
        }

