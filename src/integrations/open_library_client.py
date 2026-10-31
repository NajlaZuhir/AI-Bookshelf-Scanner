"""Metadata Module: retrieval of structured book book metadata
   searching → matching → fetching details → normalization.
"""
import sys
import requests
import re
from pathlib import Path
from difflib import SequenceMatcher
import time


# Supports both direct execution and package imports
if __package__:
    from ..config import OPEN_LIBRARY_BASE_URL
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.config import OPEN_LIBRARY_BASE_URL


# 1) Search Open Library for books matching the given title, author
def search_book(title, author=None):

    url = f"{OPEN_LIBRARY_BASE_URL.rstrip('/')}/search.json"
    params = {"title": title} if author is None else {"title": title, "author": author}

    response = requests.get(
        url, 
        params=params,
        timeout=15  # Set a timeout for the request
    )
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


# 2) Retrieve full metadata from Works API
def get_book_metadata(work_id):
    work_id = work_id.split("/")[-1]

    url = (
        f"{OPEN_LIBRARY_BASE_URL.rstrip('/')}"
        f"/works/{work_id}.json"
    )

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                timeout=(10, 20)
            )
            response.raise_for_status()
            return response.json()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ):
            if attempt == 2:
                raise

            time.sleep(2 ** attempt)


# 3) Combine and standardize fields
def normalize_book_meta_data(search_result, work_data):
    description = work_data.get("description")

    if isinstance(description, dict):
        description = description.get("value")

    # Combine the two API responses
    normalized = {
        "work_id": search_result.get("key", "").split("/")[-1],

        "title": search_result.get("title")
                 or work_data.get("title"),

        "authors": search_result.get("author_name", []),

        "description": description,

        "subjects": work_data.get("subjects", []),

        "first_publish_year": search_result.get(
            "first_publish_year"
        ),

        "cover_id": search_result.get("cover_i")
                    or (
                        work_data.get("covers") or [None]
                    )[0],

        "languages": search_result.get("language", []),

        "source": "open_library"
    }

    return normalized


# supporting functions for its metadata lookup.
# Their main purpose is to choose the Open Library search result that best matches the detected title and author, since image recognition and catalog entries may differ slightly.
def normalize_text(text):
    """removes differences in capitalization, punctuation, and extra spaces."""
    text = (text or "").casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def similarity(text_a, text_b):
    """compares two normalized strings and returns a score from 0.0 to 1.0. It measures character similarity, not similarity in meaning."""
    a = normalize_text(text_a)
    b = normalize_text(text_b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def select_best_match(books, title, author=None):
    """scores each candidate using 80% title + 20% author when an author is provided, or just the title otherwise."""
    best_book = None
    best_score = 0.0

    for book in books:
        title_score = similarity(
            title, book.get("title", "")
        )

        if author:
            author_score = max(
                (
                    similarity(author, name)
                    for name in book.get("author_name", [])
                ),
                default=0.0
            )
            score = 0.8 * title_score + 0.2 * author_score
        else:
            score = title_score

        if score > best_score:
            best_score = score
            best_book = book

    if best_score < 0.80:
        return None

    return best_book



# 4) Main function to find a book or all books, with error handling and logging
def run_find_book(title, author=None):
    if not title or not title.strip():
        return None

    search_response = search_book(title, author)
    books = search_response.get("docs", [])

    if not books:
        return None

    search_result = select_best_match(
        books, title, author
    )

    if search_result is None:
        return None

    work_data = get_book_metadata(search_result["key"])

    return normalize_book_meta_data(search_result, work_data)

def find_all_books(books, *, find_book=None):
    """Look up every detected book, preserving unmatched and failed records."""
    lookup = run_find_book if find_book is None else find_book
    results = []

    for index, book in enumerate(books, start=1):
        title = book.get("title")
        author = book.get("author")
        print(f"Processing {index}: {title} - {author}")

        try:
            metadata = lookup(title, author)
            status = "matched" if metadata else "unmatched"
        except requests.exceptions.RequestException as exc:
            print(f"Metadata API failed for {title}: {exc}")
            metadata = None
            status = "api_error"

        results.append({
            "detected_title": title,
            "detected_author": author,
            "match_status": status,
            "metadata": metadata,
        })

    return results

# Use this block for direct testing of the module
if __name__ == "__main__":
    # python -m src.integrations.open_library_client

    test_inputs = [
    'Atomic Habits, James Clear',
    'Deep Work',
    'Atomic Habits',
    'An unlikely invented title',
    'A book without description',
    'Invalid identifier',
    ]

    results = find_all_books(
    [{"title": inp.split(",")[0].strip(), "author": (inp.split(",")[1].strip() if "," in inp else None)} for inp in test_inputs]
    )

    print("\nFinal Results:")
    for res in results:
        print(res)
        print("-" * 40)
