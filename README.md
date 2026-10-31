# AI Bookshelf Scanner

AI Bookshelf Scanner identifies readable books in a bookshelf photograph,
retrieves metadata for the detected titles, and ranks the results according to
the reader's preferences.

## What it does

1. Sends a bookshelf image to OpenRouter for book-title and author detection.
2. Matches detected books with metadata from Open Library.
3. Creates semantic embeddings with
   `sentence-transformers/all-MiniLM-L6-v2`.
4. Ranks the books against a free-text reading preference.
5. Stores scans, matched books, and recommendation results in PostgreSQL.

## Technology stack

- **Language:** Python 3.11
- **API:** FastAPI with Uvicorn
- **AI book detection:** OpenRouter through the OpenAI SDK
- **Book metadata:** Open Library API through Requests
- **Recommendations:** Sentence Transformers and NumPy
- **Database:** PostgreSQL with Psycopg
- **Validation and configuration:** Pydantic and `python-dotenv`
- **Testing:** Pytest

## Setup

Follow the [setup and usage guide](docs/setup.md) to configure the environment,
install dependencies, set up PostgreSQL, run the CLI, start the API, and run
the repository tests.

## Run the CLI

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
├── data/                         # Sample bookshelf images and generated data
├── docs/                         # Setup, development, and integration guides
├── tests/                        # Repository and integration tests
├── .env.example                  # Environment configuration template
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```
