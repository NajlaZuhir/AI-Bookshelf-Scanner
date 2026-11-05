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
- **Testing:** Pytest

## Setup

Follow the [setup and usage guide](docs/setup.md) to configure the environment,
initialize PostgreSQL, and run the backend and frontend in separate terminals.
Upload a photo, review detected books, and enter your reading preferences to get
recommendations. See the [frontend guide](frontend/README.md) for UI and proxy details.

## Optional: run the CLI

From the project root, run:

```bash
python -m src.cli \
  --image "data/book_1.jpg" \
  --preference "I enjoy science fiction and fantasy" \
  --top-k 3
```

The CLI detects books in the image, retrieves their metadata, saves the scan
and recommendations to PostgreSQL, and prints the ranked results.

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
