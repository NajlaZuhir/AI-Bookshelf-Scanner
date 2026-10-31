# Manual API integration testing

Use this guide to verify that the CLI pipeline, FastAPI endpoints, and PostgreSQL work together.

## Scope

The current workflow is:

```text
CLI: image -> VLM detection -> Open Library metadata -> save scan and books
    -> generate and save an initial recommendation
API: GET the saved records -> POST another preference -> GET saved recommendations
```

`POST /scans` currently accepts a JSON image path and creates a scan record only. It does not upload an image, detect books, or populate book records. Use the CLI for those steps in this guide.

These are manual integration checks using real PostgreSQL, external providers, and the recommendation model. They are separate from repository pytest tests and automated HTTP tests. Running the CLI can consume provider API calls; repeat recommendation requests reuse saved metadata.

Successful inserts remain in the database for inspection. Repeating the CLI creates another scan. Repeating the recommendation POST creates another result for the existing scan.

## 1. Prerequisites

- PostgreSQL is running; prepare the `bookshelf_test` database using the instructions below.
- The project dependencies are installed in the active Python environment.
- `.env` contains the required PostgreSQL and OpenRouter configuration.
- The test image exists, for example `data/book_6.jpg`.
- Use Git Bash. Run all commands from the project root:

  ```bash
  cd ~/Desktop/Git25_26/Book_Shelf_Scanner_2.0/ai-bookshelf-scanner
  ```

### Test database setup

Use a separate `bookshelf_test` database. Adjust the PostgreSQL executable path
and connection details to your installation. Create the database and apply its
schema once:

```bash
PSQL="/c/Program Files/PostgreSQL/18/bin/psql.exe"

"$PSQL" -h localhost -p 5432 -U postgres -d postgres \
  -v ON_ERROR_STOP=1 -c "CREATE DATABASE bookshelf_test;"

"$PSQL" -h localhost -p 5432 -U postgres -d bookshelf_test \
  -v ON_ERROR_STOP=1 --single-transaction \
  -f src/database/migrations/001_book_shelf_schema.sql
```

Enter the PostgreSQL password when prompted. Skip database creation if it already
exists, and skip the initial schema if its tables already exist.

The current repository expects `books.authors` and `books.subjects` to use
`TEXT[]`. An older database using `JSONB` for these columns needs a separate
conversion before running the workflow. For first-time environment and database
setup, see the [setup guide](setup.md#first-time-setup).

The connection code reads `DB_NAME`. A separate `.env` entry such as `DB_test_NAME` does not select the test database automatically. The commands below override `DB_NAME` for each process without editing `.env`.

### Repository tests

After [test database setup](#test-database-setup), run:

```bash
DB_NAME=bookshelf_test python -m pytest tests/test_repositories.py -v
```

The tests insert records that remain available for inspection. They exercise the
repositories using PostgreSQL; the manual CLI and API checks follow below.

## 2. Run the CLI pipeline

In terminal A:

```bash
DB_NAME=bookshelf_test python -m src.cli \
  --image "data/book_6.jpg" \
  --preference "I enjoy science fiction and fantasy novels" \
  --top-k 3
```

Wait for the command to finish. Check that:

- There is no traceback.
- The terminal prints the recommendation count and JSON results.
- With a readable image and successfully matched books, the result contains saved book IDs and similarity scores.
- At most three books are returned. Fewer results can be valid if fewer books have usable metadata.

The CLI saves the scan, matched books, and an initial recommendation result. It does not print the new scan ID separately, so find it through `GET /scans` in the next step.

If the result is empty, inspect the metadata lookup output. Unreadable titles, unmatched books, or provider failures can result in no saved matched books. Choose an image with matched books before testing nonempty rankings.

## 3. Start the API against the same database

In terminal B, also from the project root:

```bash
DB_NAME=bookshelf_test python -m uvicorn src.api.main:app --reload
```

Keep this terminal running. If a server already uses port 8000, stop that server with Ctrl+C in its terminal, then start the command above. Confirm startup succeeds without an address-in-use error.

Both commands must use `bookshelf_test`: setting `DB_NAME` for the CLI does not change the environment of an already-running API server.

Open Swagger UI:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

For each Swagger request, expand the endpoint, click **Try it out**, enter its parameters/body, and click **Execute**. Click Execute again to retrieve updated data; previously displayed responses do not update automatically.

## 4. Find and retrieve the saved scan

Execute:

```text
GET /scans
```

Expected: `200 OK`, with a JSON list of scans ordered by creation time, newest first.

Find the newly created scan by its image path and creation time. Copy its `scan_id`. Windows paths may appear as `data\\book_6.jpg` in JSON because backslashes are escaped.

The IDs below are examples only. Use the actual IDs from your run.

For example, if the new scan ID is 26, execute:

```text
GET /scans/26
GET /scans/26/books
```

Check that:

- Both requests return `200 OK`.
- The scan response has `scan_id: 26` and the expected image path.
- The books response contains the matched books for that scan.
- Each book has an integer `book_id` and nested `metadata`, including title, authors, description, and subjects.

Record the returned book IDs. Retrieve one individually with `GET /books/{book_id}` and compare it with the corresponding item in the scan's book list.

For curl examples, open another Git Bash terminal and set your actual scan ID:

```bash
SCAN_ID=26  # Example: replace with the ID returned for your run.
curl -i "http://127.0.0.1:8000/scans/$SCAN_ID"
curl -i "http://127.0.0.1:8000/scans/$SCAN_ID/books"
```

## 5. Generate recommendations from the saved books

In Swagger, execute `POST /scans/{scan_id}/recommendations` using the scan ID from step 4 and this JSON body:

```json
{
  "preference_text": "I enjoy poetry and literary fiction",
  "top_k": 3
}
```

Equivalent Git Bash request:

```bash
curl -i -X POST \
  "http://127.0.0.1:8000/scans/$SCAN_ID/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"preference_text":"I enjoy poetry and literary fiction","top_k":3}'
```

Expected: `201 Created`, with a response containing:

- An integer `result_id`.
- The requested `scan_id`.
- A `recommendations` list containing up to three books.

Check that every recommended `book_id` belongs to the saved books from step 4. Similarity scores should be in descending order. The model may need time to load on the first request.

Record the new `result_id` for the retrieval checks.

## 6. Retrieve the saved recommendation

In Swagger, execute:

```text
GET /recommendations/{result_id}
GET /scans/{scan_id}/recommendations
```

Use the actual IDs from steps 4 and 5. Both requests should return `200 OK`.

The individual result should contain:

- The correct result and scan IDs.
- The preference text submitted in step 5.
- The stored model name and `top_k`.
- A `ranked_outcome` matching the POST response's `recommendations` list.

The scan history should include both the initial CLI recommendation and the new API-created result, newest first.

You can also verify `GET /books` and `GET /recommendations` return `200 OK` and include the corresponding records. These endpoints return records from other runs as well, so compare IDs rather than expecting a fixed total count.

## 7. Repeat the request without rescanning

Repeat step 5 for the same scan ID with another preference:

```json
{
  "preference_text": "I enjoy mythology and adventure stories",
  "top_k": 2
}
```

Check that:

- The POST returns `201 Created` with a new `result_id` and the same `scan_id`.
- There are at most two recommendations.
- `GET /scans/{scan_id}/books` returns the same saved book IDs as before.
- The recommendation history grows by one and stores the new preference.
- No new scan is created by this POST, and the original CLI scan is reused.

Different preferences can produce the same ordering for some book collections. A different ranking is not required for the request to be correct; confirm the new preference and new result were persisted.

## 8. Check the records directly in PostgreSQL

In pgAdmin or your database viewer, select **bookshelf_test** and refresh the tables or rerun the queries. Replace the example scan ID 26 with your actual ID:

```sql
SELECT current_database();

SELECT scan_id, image_path, created_at
FROM scan
WHERE scan_id = 26;

SELECT book_id, scan_id, work_id, title, authors, description, subjects
FROM books
WHERE scan_id = 26
ORDER BY book_id;

SELECT result_id, scan_id, model_name, preference_text,
       top_k, ranked_outcome, created_at
FROM recommendation_result
WHERE scan_id = 26
ORDER BY created_at DESC, result_id DESC;
```

Check that the database values match the HTTP responses. Every recommended book ID inside `ranked_outcome` should belong to that scan's saved books. The JSON field itself does not enforce a foreign key to individual books, so inspect those IDs explicitly.

## 9. Optional: test POST /scans separately

This endpoint registers an image path only. It does not call the VLM or Open Library.

In Swagger, execute `POST /scans` with:

```json
{
  "image_path": "data/book_6.jpg"
}
```

Expected: `201 Created`, returning a new `scan_id`. Retrieve it through `GET /scans/{scan_id}`.

The new scan has no books or recommendation history, so these requests should return `200 OK` with `[]`:

```text
GET /scans/{scan_id}/books
GET /scans/{scan_id}/recommendations
```

Use the populated CLI scan from step 4 for nonempty recommendation checks.

## 10. Optional: basic error handling checks

Run these in Swagger. For nonexistent-record checks, first confirm the chosen ID is absent. Do not assume a large positive ID will always be missing.

| Request | Input | Expected |
| --- | --- | --- |
| GET `/scans/{scan_id}` | Confirmed nonexistent integer ID | `404` |
| GET `/books/{book_id}` | Confirmed nonexistent integer ID | `404` |
| GET `/recommendations/{result_id}` | Confirmed nonexistent integer ID | `404` |
| GET `/scans/{scan_id}/books` | Confirmed nonexistent scan | `404` |
| POST `/scans/{scan_id}/recommendations` | Confirmed nonexistent scan, valid request body | `404` |
| POST `/scans/{scan_id}/recommendations` | Existing scan, `top_k: 0` or `top_k: -1` | `422` |
| POST `/scans/{scan_id}/recommendations` | Existing scan, `top_k: true` or `top_k: 1.5` | `422` |
| POST `/scans/{scan_id}/recommendations` | Existing scan, blank `preference_text` | `422` |
| POST `/scans` | Missing or blank `image_path` | `422` |
| GET `/scans/not-an-integer` | Noninteger path parameter | `422` |

Invalid recommendation requests should not create new results. Compare the scan's recommendation history before and after each request.

`top_k: null` is allowed and requests all rankable books. Omitting `top_k` uses the default of 3. A nonexistent image path submitted to the current POST `/scans` is not a file-validation test: this endpoint stores path text and does not open the file.

Image-upload checks, corrupt-image handling, simulated upstream timeouts, and automated FastAPI TestClient tests are separate work. Do not mark those as verified by this manual success-path run.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| CLI scan is absent from Swagger | Ensure both the CLI and running API use `DB_NAME=bookshelf_test`. Stop an old API server before restarting. Execute GET again in Swagger. |
| Server cannot bind port 8000 | Another server is already running. Stop it in its terminal, then restart the intended server. |
| Tables appear empty in the database viewer | Select `bookshelf_test`, refresh the table view, and rerun SELECT. |
| GET returns an empty books list | Confirm the scan came from the CLI and that metadata lookups produced matched books. A POST-created path-only scan starts empty. |
| POST returns `422` | Check the JSON body, required fields, and that `top_k` is a positive JSON integer, not a quoted string or boolean. |
| POST returns `404` | Use a scan ID that exists in the same database used by the API server. |
| Recommendation request takes time | Check server logs; the embedding model may be loading for the first request. |

## Record the result

For each manual run, note the date, image, scan ID, returned book IDs, result IDs, submitted preferences, and observed status codes. Mark only checks actually performed:

- [ ] CLI completed with matched books saved in `bookshelf_test`.
- [ ] GET scan, book list, and individual book responses matched the saved data.
- [ ] Recommendation POST returned `201` and valid ranked book IDs.
- [ ] GET individual result and history matched the POST and database records.
- [ ] A second preference created another result without creating another scan.
- [ ] PostgreSQL inspection confirmed the scan, books, and results share the expected IDs.
- [ ] Optional path-only scan creation and empty-list behavior were checked.
- [ ] Optional error cases were checked.

Completing this checklist documents manual CLI-to-API-to-database integration testing. Automated HTTP integration tests remain a separate task.
