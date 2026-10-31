# Manual API integration testing

Verify the CLI, FastAPI, and PostgreSQL together: scan an image, retrieve its
books, generate another recommendation, and check the saved records.

## 1. Prerequisites

Complete the [environment setup](setup.md#first-time-setup), activate your Conda
environment, and keep PostgreSQL running. Use Git Bash from the project root.

### Test database setup

Use a separate `bookshelf_test` database. Adjust the executable path and connection
details for your installation:

```bash
PSQL="/c/Program Files/PostgreSQL/18/bin/psql.exe"

"$PSQL" -h localhost -p 5432 -U postgres -d postgres \
  -v ON_ERROR_STOP=1 -c "CREATE DATABASE bookshelf_test;"

"$PSQL" -h localhost -p 5432 -U postgres -d bookshelf_test \
  -v ON_ERROR_STOP=1 --single-transaction \
  -f src/database/migrations/001_book_shelf_schema.sql
```

Skip database creation if it exists, and skip the schema if its tables exist.
All commands below use `DB_NAME=bookshelf_test` without changing `.env`.
Test records remain in this database for inspection.

### Repository tests

```bash
DB_NAME=bookshelf_test python -m pytest tests/test_repositories.py -v
```

These test database repositories. Continue below to check the full workflow.

## 2. Scan an image

```bash
DB_NAME=bookshelf_test python -m src.cli \
  --image "data/book_6.jpg" \
  --preference "I enjoy science fiction and fantasy novels" \
  --top-k 3
```

Expect no traceback and up to three recommendations with book IDs and similarity
scores. The CLI saves the scan, matched books, and initial recommendation. Use an
image with matched books to check nonempty results; scanning calls external APIs.

## 3. Start the API

In another terminal, activate the same environment and run from the project root:

```bash
DB_NAME=bookshelf_test python -m uvicorn src.api.main:app --reload
```

Keep it running and open [Swagger UI](http://127.0.0.1:8000/docs).
For each request, select **Try it out**, enter the values, and select **Execute**.
Both the CLI and API must use the test database.

## 4. Retrieve the scan and books

Call `GET /scans`, find the new scan by image path and creation time, and copy its
`scan_id`. Use actual IDs from your run in all requests:

| Request | Expected |
| --- | --- |
| `GET /scans/{scan_id}` | `200`; correct image path and scan ID |
| `GET /scans/{scan_id}/books` | `200`; matched books with IDs and nested metadata |
| `GET /books/{book_id}` | `200`; matches a book from that scan |

Record the book IDs for the next checks.

## 5. Generate and retrieve recommendations

Call `POST /scans/{scan_id}/recommendations` with:

```json
{
  "preference_text": "I enjoy poetry and literary fiction",
  "top_k": 3
}
```

Expect `201`, a new `result_id`, the same `scan_id`, and up to three
`recommendations`. Book IDs must belong to the scan, with similarity scores in
descending order.

Then check:

| Request | Expected |
| --- | --- |
| `GET /recommendations/{result_id}` | `200`; saved preference, model, limit, and `ranked_outcome` matching the POST results |
| `GET /scans/{scan_id}/recommendations` | `200`; includes CLI and API results, newest first |
| `GET /books` and `GET /recommendations` | `200`; include the saved records |

Repeat the POST with a different preference and `top_k: 2`. Expect a new result,
the same scan and book IDs, and at most two recommendations. The history should
grow by one; a different ranking is not required.

## 6. Verify PostgreSQL records

In your database viewer, select `bookshelf_test` and replace `26` with your scan ID:

```sql
SELECT current_database();

SELECT * FROM scan WHERE scan_id = 26;

SELECT * FROM books WHERE scan_id = 26 ORDER BY book_id;

SELECT * FROM recommendation_result
WHERE scan_id = 26
ORDER BY created_at DESC, result_id DESC;
```

Confirm IDs, metadata, preferences, and ranked results match the API responses.

## Optional checks

`POST /scans` with `{"image_path": "data/book_6.jpg"}` should return `201` and a
new scan ID. It only registers a path: it does not upload or scan the image.
Its book list and recommendation history should return `200` with `[]`.

| Request / input | Expected |
| --- | --- |
| GET a scan, book, or recommendation using an ID confirmed absent | `404` |
| POST recommendations for an absent scan with a valid body | `404` |
| POST recommendations with `top_k: 0`, `-1`, `true`, or `1.5` | `422` |
| POST recommendations with a blank preference | `422` |
| POST a scan with a missing or blank image path | `422` |
| `GET /scans/not-an-integer` | `422` |

Invalid recommendation requests must not add saved results. Omitting `top_k`
defaults to 3; `top_k: null` requests all rankable books.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| CLI records missing from the API | Ensure both processes use `bookshelf_test`; restart an old API server and execute GET again |
| Port 8000 unavailable | Stop the existing server before starting another |
| Empty book list | Use a CLI-created scan with matched books; POST /scans creates a path-only record |
| Recommendation request takes time | The embedding model may be loading |
| Database viewer shows old data | Select `bookshelf_test` and refresh or rerun the query |

Record the date, image, scan ID, book IDs, result IDs, and checks performed.
These manual checks do not replace automated HTTP tests or provider-failure tests.
