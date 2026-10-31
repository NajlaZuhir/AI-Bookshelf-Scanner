
# DB_NAME=bookshelf_test python -m pytest src/database/repositories/test_repos.py -v
import uuid
from datetime import datetime

import pytest
from psycopg.errors import ForeignKeyViolation

from src.database.connection import get_connection
from src.database.repositories.scan_repository import ScanRepository
from src.database.repositories.book_repository import BookRepository
from src.database.repositories.recommendation_repository import RecommendationResultRepository

image_path = f"test {uuid.uuid4().hex[:8]}.jpg"
book = {
    "metadata": {
        "work_id": f"test {uuid.uuid4().hex[:8]}",
        "title": f"test {uuid.uuid4().hex[:8]}",
        "authors": ["Testing"],
        "description": "This is a test book for unit testing purposes.",
        "subjects": ["Test", "Unit Testing"],
    }
}


@pytest.fixture
def scan_id():
    """Create a scan and keep its records for inspection after the test."""
    return ScanRepository().create(image_path)


@pytest.fixture
def missing_id():
    """Find an ID absent from all three tables, including on repeated runs."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT LEAST(0, COALESCE(MIN(id), 0)) - 1
                FROM (
                    SELECT scan_id AS id FROM scan
                    UNION ALL
                    SELECT book_id AS id FROM books
                    UNION ALL
                    SELECT result_id AS id FROM recommendation_result
                ) AS existing_ids;
            """)
            return cur.fetchone()[0]


def test_scan_repository(scan_id, missing_id):
    repo = ScanRepository()

    assert isinstance(scan_id, int)

    retrieved = repo.get_by_id(scan_id)
    assert retrieved["image_path"] == image_path

    assert repo.get_by_id(missing_id) is None


def test_book_repository(scan_id, missing_id):
    repo = BookRepository()

    book_id = repo.create(scan_id, book)
    assert isinstance(book_id, int)

    retrieved = repo.get_by_id(book_id)
    assert retrieved["metadata"] == book["metadata"]

    assert repo.get_by_id(missing_id) is None

# ADDITIONAL TESTS FOR RECOMMENDATION_RESULT_REPOSITORY AND BOOK_REPOSITORY
def test_recommendation_result_repository(scan_id, missing_id):
    book_id = BookRepository().create(scan_id, book)

    ranked_outcome = [
        {
            "book_id": book_id,
            "rank": 1,
            "similarity": 0.95,
        }
    ]

    repo = RecommendationResultRepository()
    result_id = repo.create(
        scan_id,
        "test_model",
        "test preference",
        1,
        ranked_outcome,
    )
    assert isinstance(result_id, int)

    retrieved = repo.get_by_id(result_id)
    assert retrieved is not None
    assert retrieved["scan_id"] == scan_id
    assert retrieved["model_name"] == "test_model"
    assert retrieved["preference_text"] == "test preference"
    assert retrieved["top_k"] == 1
    assert retrieved["ranked_outcome"] == ranked_outcome

    assert repo.get_by_id(missing_id) is None
    assert repo.get_by_scan_id(missing_id) == []


def test_books_filtered_by_scan(scan_id):
    repo = BookRepository()
    other_scan_id = ScanRepository().create(f"other-{uuid.uuid4().hex}.jpg")

    first_book_id = repo.create(scan_id, book)
    second_book_id = repo.create(scan_id, book)
    other_book_id = repo.create(other_scan_id, book)

    retrieved = repo.get_by_scan(scan_id)
    assert [record["book_id"] for record in retrieved] == [
        first_book_id,
        second_book_id,
    ]
    assert [record["book_id"] for record in repo.get_by_scan(other_scan_id)] == [
        other_book_id,
    ]


def test_recommendation_history_by_scan(scan_id):
    repo = RecommendationResultRepository()
    books = BookRepository()
    other_scan_id = ScanRepository().create(f"other-{uuid.uuid4().hex}.jpg")
    book_id = books.create(scan_id, book)
    other_book_id = books.create(other_scan_id, book)
    ranked = [{"book_id": book_id, "rank": 1, "similarity": 0.95}]
    other_ranked = [{"book_id": other_book_id, "rank": 1, "similarity": 0.9}]

    first_id = repo.create(scan_id, "test_model", "first preference", 1, ranked)
    second_id = repo.create(scan_id, "test_model", "second preference", 1, ranked)
    third_id = repo.create(scan_id, "test_model", "third preference", 1, ranked)
    other_id = repo.create(other_scan_id, "test_model", "other preference", 1, other_ranked)

    # Control only these test rows to verify timestamp order and tied timestamps.
    newer = datetime(2026, 1, 2)
    older = datetime(2026, 1, 1)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "UPDATE recommendation_result SET created_at = %s WHERE result_id = %s",
                [(newer, first_id), (older, second_id), (newer, third_id)],
            )

    history = repo.get_by_scan_id(scan_id)
    assert [record["result_id"] for record in history] == [
        third_id,
        first_id,
        second_id,
    ]
    assert all(record["scan_id"] == scan_id for record in history)
    assert [record["created_at"] for record in history] == [newer, newer, older]
    assert [record["result_id"] for record in repo.get_by_scan_id(other_scan_id)] == [
        other_id,
    ]


def test_book_nonexistent_scan(missing_id):
    assert ScanRepository().get_by_id(missing_id) is None

    repo = BookRepository()
    with pytest.raises(ForeignKeyViolation) as error:
        repo.create(missing_id, book)

    assert error.value.diag.table_name == "books"
    assert repo.get_by_scan(missing_id) == []
