# Manual API integration testing

The guide checks: **upload → detect books → retrieve metadata → save → retrieve
records → recommend**. Use Swagger UI or curl to exercise the API directly.

Uploading a photo saves a scan and matched books. Recommendations are generated
in a separate request. Scanning calls the real vision and metadata services.

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

These are optional automated database repository checks. The manual API
workflow starts below.

## 2. Start the API

With the Python environment activated, run from the project root:

```bash
DB_NAME=bookshelf_test python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Keep it running and open [Swagger UI](http://127.0.0.1:8000/docs).
For each request, select **Try it out**, enter the values, and select **Execute**.

## 3. Upload and scan an image

In Swagger, expand `POST /scans`, choose a sample such as `data/book_6.jpg` in
the `file` field, and execute. Alternatively, use a second Git Bash terminal
from the project root:

```bash
curl -i -X POST http://127.0.0.1:8000/scans \
  -F "file=@data/book_6.jpg"
```

Expect `201` with `scan_id`, `total_detected`, `total_matched`, `total_unmatched`,
`total_api_errors`, and a `books` array. Copy the returned scan ID. Matched books
should include `book_id` and metadata. Unmatched books and lookup failures
appear in this response but are not saved as book records.

The uploaded image is stored under a unique JPEG filename in `data/uploads/`.
An image with no readable titles can return a successful scan with no books.
Use a scan with matched books to check nonempty recommendations.

## 4. Retrieve the scan and books

Use the `scan_id` from the upload response. `GET /scans` should also include the
new scan. Use actual IDs from your run in all requests:

| Request | Expected |
| --- | --- |
| `GET /scans/{scan_id}` | `200`; correct image path and scan ID |
| `GET /scans/{scan_id}/books` | `200`; matched books with IDs and nested metadata |
| `GET /books/{book_id}` | `200`; matches a book from that scan |

Record the book IDs for the next checks.
Before generating recommendations, `GET /scans/{scan_id}/recommendations`
should return `200` with `[]` for this new upload.

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
| `GET /scans/{scan_id}/recommendations` | `200`; includes the newly saved result, newest first |
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

Uploads use multipart form data with the field name `file`. The limits are
10 MB and 20 megapixels, and accepted formats are JPEG and PNG.

| Request / input | Expected |
| --- | --- |
| GET a scan, book, or recommendation using an ID confirmed absent | `404` |
| POST recommendations for an absent scan with a valid body | `404` |
| POST recommendations with `top_k: 0`, `-1`, `true`, or `1.5` | `422` |
| POST recommendations with a blank preference | `422` |
| POST a scan without the `file` field | `422` |
| Upload an empty or unreadable image | `400` |
| Upload a readable image in an unsupported format, such as GIF | `415` |
| Upload an image exceeding the file-size or pixel limit | `413`; Pillow decompression-bomb rejection can return `400` |
| `GET /scans/not-an-integer` | `422` |

Invalid recommendation requests must not add saved results. Omitting `top_k`
defaults to 3; `top_k: null` requests all rankable books.

## Optional: use the CLI instead of uploading

With the same test database selected, run from the project root:

```bash
DB_NAME=bookshelf_test python -m src.cli \
  --image "data/book_6.jpg" \
  --preference "I enjoy science fiction and fantasy novels" \
  --top-k 3
```

The CLI saves both the scan and an initial recommendation. Find its scan ID via
`GET /scans`, then follow the retrieval steps above. Both the CLI and API must
use `bookshelf_test` to see the same records.

