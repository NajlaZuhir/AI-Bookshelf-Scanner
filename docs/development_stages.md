
# Stage 1: Problem Definition & Planning

Help readers choose books in bookstores, book fairs, or libraries using a bookshelf photo and their reading preferences or history.

This stage focused on defining requirements and exploring the initial architecture before implementation.

**Proposed workflow:** Photo + reader preferences/history → book identification → book information → ranked recommendations.

## Scope

- Identify books in an image.
- Retrieve relevant book information.
- Rank detected books based on the reader's interests and history.
- Provide a short explanation for each recommendation.

The current MVP uses free-text preferences. Persistent reading history and
recommendation explanations remain planned features.

## Technologies considered

GPT vision models, OCR, Google Vision, PostgreSQL, React, and book metadata APIs. No technology choices were finalized at this stage.

## Possible success metrics

Book identification accuracy, metadata match rate, recommendation relevance, and response time.

# Stage 2: Data Engineering / Book Metadata

Built a reusable metadata lookup service, `run_find_book(title, author=None)`, to turn a title and optional author into structured book data.

## Data source

Evaluated Google Books, Open Library, and Goodreads. Open Library became the working source after Google Books returned quota errors (`429 RESOURCE_EXHAUSTED`).

## Workflow

Title + optional author → search → select and validate best match → fetch work details → normalize metadata.

- `/search.json`: retrieves book candidates and basic metadata.
- `/works/{work_id}.json`: retrieves descriptions and subjects.
- Matching uses normalized text similarity, weighting title more heavily than author and rejecting low-confidence results.

## Output and validation

Normalized fields: `work_id`, `title`, `authors`, `description`, `subjects`, `first_publish_year`, `cover_id`, `languages`, and `source`.

Manual checks covered *Atomic Habits*, *Deep Work*, nonexistent titles, invalid identifiers, and books without descriptions.

Used Postman to explore Google Books and Open Library before implementing the Python integrations. Inspected request parameters, JSON fields, and error responses, including Google Books quota errors. Testing Open Library's search and work-details endpoints helped define the metadata mapping and normalization.

Added a shared PostgreSQL metadata cache keyed by normalized title and author.
Successful matches are reused for 30 days; missing or expired entries trigger
an Open Library lookup and refresh. Unmatched titles and API failures are not
cached. Cache access failures fall back to the normal lookup, and terminal
messages report cache hits, misses, and saves.

# Stage 3: AI / Computer Vision

Built `identify_books_in_image(image_path)` to extract readable book titles and authors from bookshelf photos.

## Approach

Explored PaddleOCR and EasyOCR, but setup complexity and disorganized text output led to using a vision-language model through OpenRouter.

## Workflow

Bookshelf photo → vision model → structured book detections → Open Library metadata lookup.

- Sends the image as Base64 with instructions to read left to right, shelf by shelf from top to bottom.
- Prompts the model to omit unreadable titles and use `null` for unreadable authors.
- Passes detected titles and authors to the Stage 2 metadata service.

## Output and validation

Returns a `books` array containing `book_number`, `title`, and `author`. The prompt requests an empty array when no titles are readable.

Uses a strict JSON schema and Pydantic validation to reject malformed responses. Recognition accuracy still requires evaluation against manually labeled images.

## Optional Google Vision fallback

`detect_books()` calls OpenRouter first. When enabled, primary API failures or
invalid structured output trigger Google Vision Document Text Detection.
Valid empty primary responses do not trigger fallback.

OCR paragraphs are treated as candidate titles with unknown authors and passed
through the existing cached metadata matcher. Duplicate matched work IDs are
removed. Scan responses include `detection_source`; terminal output identifies
the selected provider. If both providers fail, the scan reports an error.

The fallback is disabled until Google Cloud authentication is configured and
`GOOGLE_VISION_FALLBACK_ENABLED=true` is set. OCR grouping is a baseline heuristic,
so its candidate counts are not confirmed book counts and its quality still
requires evaluation. Setup is documented in the [setup guide](setup.md#optional-google-vision-fallback).

# Stage 4: Machine Learning Recommendation

Built `recommend_books(books, user_preference, top_k=3)` to rank detected books by their relevance to the reader's stated interests.

## Approach

Uses content-based recommendation with the pretrained Sentence Transformers model `all-MiniLM-L6-v2` to compare book metadata with free-text preferences.

## Workflow

Book metadata + reader preference → text profiles → semantic embeddings → cosine similarity → ranked recommendations.

- Builds book profiles from subjects and descriptions, falling back to the title when both are missing.
- Generates normalized embeddings for the preference and book profiles.
- Scores each book against the preference and returns the highest-scoring results, with three recommendations by default.

## Output and validation

Returns titles, authors, similarity scores, Open Library work IDs, and database book IDs when available.

Rejects blank preferences and invalid `top_k` values. Books without usable profiles are skipped; an empty candidate set returns an empty list. Setting `top_k=None` returns all ranked books.

# Stage 5: Database + Backend Integration

Connected book detection, metadata retrieval, and recommendation ranking to PostgreSQL through `process_bookshelf(image_path, user_preference, top_k=3)`.

## Database structure

- `scan`: image path and scan timestamp.
- `books`: matched book metadata linked to a scan.
- `recommendation_result`: reader preference, model name, result limit, and ranked results stored as JSONB.

Foreign keys link books and recommendation results to their scan.

## Backend workflow

Image → detect books → retrieve metadata → save scan and matched books → rank saved books → save recommendations.

Uses Psycopg and repository classes to separate database queries from application logic. Connection settings come from environment variables.

Saved book IDs are retained in recommendations. The backend can reuse a scan's stored books for new preferences and retrieve its recommendation history.

## Image-upload API

Added `POST /scans` to accept a multipart image in the `file` field. It validates
JPEG/PNG contents, enforces 10 MB and 20-megapixel limits, corrects orientation,
and stores a normalized JPEG in `data/uploads/` under a unique filename.

`process_scan(image_path)` reuses the detection and metadata services. The scan
and matched books share one database transaction; a saving failure rolls back
their inserts. Failed upload processing also removes the uploaded image.

The response includes the scan ID, detection counts, lookup statuses, and saved
book IDs. Unmatched titles and metadata lookup failures remain in the response;
only matched books are persisted. Recommendations are generated separately via
`POST /scans/{scan_id}/recommendations`, allowing preference changes without
rescanning.

## Validation

Used Postman to manually test GET requests to `/books`, `/scans`, and `/recommendations`, plus POST requests for scan creation and recommendations. Checked request handling, API responses, and database retrieval through the flow: Postman → FastAPI → repositories → PostgreSQL.

These were manual integration checks, separate from automated repository tests covering record creation and retrieval, filtering by scan, recommendation history, and foreign-key enforcement. A [manual integration guide](manual_api_integration_testing.md) documents the current upload, retrieval, recommendation, and database checks, with the CLI as an alternative.

# Stage 6: Frontend Development

Built a responsive React + Vite interface with a cream-and-green design.

## Workflow

Select or drop a photo → preview → scan → review detected books → enter
preferences → display up to three recommendations.

- Displays detected titles, authors, available descriptions, and match statuses.
- Includes loading indicators, request errors, empty results, and starting a new scan.
- Shows ranked recommendations with available metadata and Open Library links.
- Clears previous results when the photo changes; recommendations use matched books.

During development, Vite forwards `/api` requests to FastAPI on port 8000 and
removes the `/api` prefix. The backend and frontend run in separate terminals.

## Remaining work

Deployment, device-based sessions, persistent reader preferences and reading
history, rate limiting, and production monitoring
remain future work. AI/ML quality evaluation is also pending.
