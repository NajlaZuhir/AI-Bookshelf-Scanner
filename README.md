# AI Bookshelf Scanner

AI Bookshelf Scanner identifies readable books in a bookshelf photograph,
retrieves metadata for the detected titles, and ranks the results according to
the reader's preferences.

## What it does

1. Accepts a bookshelf photo through a React web interface or the CLI.
2. Detects readable book titles and authors using OpenRouter, with optional Google Vision OCR fallback on detection failure.
3. Retrieves and matches book metadata from Open Library, reusing a shared 30-day PostgreSQL cache.
4. Ranks matched books against free-text reading preferences using MiniLM embeddings.
5. Stores scans, matched books, and recommendation results in PostgreSQL.
6. Displays detected books, match statuses, and personalized recommendations.
7. Limits API scan requests per client IP to reduce abuse and external API usage.

## Web workflow

```text
Upload bookshelf photo
        ↓
Check rate limit
        ↓
Validate and save image
        ↓
OpenRouter identifies titles and authors
        ↓
Google Vision fallback if recognition fails
        ↓
Check metadata cache
   ├─ Hit → reuse metadata
   └─ Missing or expired → fetch from Open Library → cache
        ↓
Save scan and matched books in PostgreSQL
        ↓
Display detected books
        ↓
Reader enters preferences
        ↓
MiniLM embeddings + similarity ranking
        ↓
Save and display recommendations
```

## Technology stack

- **Languages:** Python 3.11 and JavaScript
- **Frontend:** React and Vite
- **API:** FastAPI with Uvicorn
- **Image uploading:** FastAPI UploadFile, `python-multipart`, and Pillow
- **AI book detection:** OpenRouter through the OpenAI SDK
- **Optional OCR fallback:** Google Cloud Vision
- **Book metadata:** Open Library API through Requests
- **Recommendations:** Sentence Transformers and NumPy
- **Database:** PostgreSQL with Psycopg
- **Validation and configuration:** Pydantic and `python-dotenv`
- **Rate limiting:** SlowAPI with in-memory counters
- **Testing:** Pytest

## Setup

Install Conda, PostgreSQL, and Node.js. In Git Bash, from the project root:

```bash
conda create -n bookshelf python=3.11 -y
conda activate bookshelf
python -m pip install -r requirements.txt
cp .env.example .env
```

Keep an existing `.env` if configured. Set your OpenRouter API key and PostgreSQL
credentials in `.env`.

With PostgreSQL running, create the database and apply the schema. Adjust the
executable path and connection details for your installation:

```bash
PSQL="/c/Program Files/PostgreSQL/18/bin/psql.exe"
"$PSQL" -h localhost -p 5432 -U postgres -d postgres -c "CREATE DATABASE book_shelf;"
"$PSQL" -h localhost -p 5432 -U postgres -d book_shelf -v ON_ERROR_STOP=1 -f src/database/migrations/001_book_shelf_schema.sql
```

Skip database creation if it already exists.

## Run

Backend, from the project root:

```bash
conda activate bookshelf
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually [localhost:5173](http://localhost:5173).
Keep PostgreSQL and both terminals running. Repeat `npm install` only when
dependencies change.

Upload a JPEG/PNG photo (up to 10 MB and 20 megapixels), review detected books,
then enter preferences to get recommendations. Images go in `data/uploads/`;
scans, matched books, and recommendations are saved in PostgreSQL.

API documentation: [Swagger UI](http://127.0.0.1:8000/docs).
If Vite reports `ECONNREFUSED`, check that the backend is running on port 8000.
Vite forwards `/api` to the backend during development; production hosting
needs equivalent routing with the prefix removed.

## Optional: run the CLI

From the project root, run:

```bash
python -m src.cli --image "data/book_1.jpg" --preference "Science fiction and fantasy" --top-k 3
```

## Development

Development followed an iterative process:

**Research → choose an approach → implement a component → test manually → integrate with the next stage.**

See the [development stages](docs/development_stages.md) for the project’s
progression and implementation details.

## Project structure

```text
├── src/
│   ├── cli.py                    # CLI entry point
│   ├── config.py                 # Environment and model configuration
│   ├── integrations/             # OpenRouter and Open Library clients
│   ├── services/                 # Detection, metadata, and recommendation workflows
│   ├── ml/                       # Preprocessing, embeddings, and ranking
│   ├── database/                 # PostgreSQL schema and repositories
│   └── api/                      # FastAPI application and routes
├── frontend/                     # React interface and Vite configuration
├── data/                         # Sample images, local uploads, and generated data
├── docs/                         # Setup, development, and integration guides
├── tests/                        # PostgreSQL repository tests
├── .env.example                  # Environment configuration template
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```
## Checks

Create a separate `bookshelf_test` database and apply the same schema using the
database commands above with that name. Then run:

```bash
DB_NAME=bookshelf_test python -m pytest tests/test_repositories.py -v
```

Tests leave records in the test database. For a manual API check in Swagger,
upload through `POST /scans`, retrieve `GET /scans/{scan_id}/books`, then call
`POST /scans/{scan_id}/recommendations` with:

```json
{"preference_text": "Science fiction", "top_k": 3}
```

Frontend production build: run `npm run build` inside `frontend/`.

## Configuration

- `SCAN_RATE_LIMIT` defaults to `3/minute;20/hour` per IP. Excess API scans return
  `429`. Counters reset on backend restart; CLI scans bypass the limit.
- Optional OCR fallback: install `google-cloud-vision`, configure Google Cloud
  credentials and the Vision API, then set `GOOGLE_VISION_FALLBACK_ENABLED=true`.

Restart the backend after changing `.env`.
