# AI Book Shelf Scanner 

Identify books in a bookshelf photo and rank them based on the reader's preferences.

## First-time setup

The commands below use Git Bash on Windows. Install Conda and PostgreSQL first,
and make sure the PostgreSQL server is running. Run all commands from the
`ai-bookshelf-scanner/` directory, which contains this README and `requirements.txt`.

### 1. Create and activate a Conda environment

```bash
conda create -n bookshelf python=3.11 -y
conda activate bookshelf
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

For a new checkout, copy the configuration template. If `.env` already exists,
keep it and check its settings instead of replacing it.

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `OPENROUTER_API_KEY`: your OpenRouter API key.
- `DB_HOST` and `DB_PORT`: the PostgreSQL address, normally `localhost` and `5432`.
- `DB_NAME`: the application database name, `book_shelf` in the examples below.
- `DB_USER` and `DB_PASSWORD`: your PostgreSQL login credentials.

You can optionally set `OPENROUTER_MODEL` to select a model that supports image
input and structured JSON output. Otherwise, the code uses the default configured
in `src/config.py`.

### 4. Create the PostgreSQL database

Set the path to `psql`. This example uses PostgreSQL 18; adjust the path to match
your installation. If `psql` is already on your PATH, use `PSQL=psql` instead.

```bash
PSQL="/c/Program Files/PostgreSQL/18/bin/psql.exe"
```

Create the database once, entering the PostgreSQL password when prompted:

```bash
"$PSQL" -h localhost -p 5432 -U postgres -d postgres \
  -v ON_ERROR_STOP=1 -c "CREATE DATABASE book_shelf;"
```

Use the same host, port, user, and database name as your `.env`. If the database
already exists, skip its creation.

### 5. Apply the initial database schema

For a new, empty database, create the tables and foreign keys:

```bash
"$PSQL" -h localhost -p 5432 -U postgres -d book_shelf \
  -v ON_ERROR_STOP=1 --single-transaction \
  -f src/database/migrations/001_book_shelf_schema.sql
```

The initial schema uses `TEXT[]` for book authors and subjects, and `JSONB` for
recommendation results. Skip this step if these tables already exist; the initial
schema is not a migration to rerun on every launch.

### 6. Run the CLI

```bash
python -m src.cli \
  --image "data/book_1.jpg" \
  --preference "I enjoy science fiction and fantasy" \
  --top-k 3
```

Both `--image` and `--preference` are required. `--top-k` is optional and defaults
to `3`. Use `python -m src.cli --help` to see the available arguments.

The CLI calls OpenRouter and Open Library, saves matched books to PostgreSQL,
and generates and saves recommendations. The embedding model may download its
weights on the first run.

## Running the project again

From the project root, activate the environment and run the CLI. Keep PostgreSQL
running; the database and schema only need to be set up once.

```bash
conda activate bookshelf
python -m src.cli --image "data/book_1.jpg" --preference "I enjoy science fiction and fantasy" --top-k 3
```

Each CLI run creates a new scan and recommendation result.

## Optional: start the API

From the project root with the environment activated:

```bash
python -m uvicorn src.api.main:app --reload
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
See the [manual integration guide](docs/manual_api_integration_testing.md) to
check the CLI, database, and API together.

## Optional: run repository tests

Use a separate `bookshelf_test` database. The repository tests insert records
that remain available for inspection. Create this database and apply its schema
once, using the same `PSQL` variable from setup:

```bash
"$PSQL" -h localhost -p 5432 -U postgres -d postgres \
  -v ON_ERROR_STOP=1 -c "CREATE DATABASE bookshelf_test;"
"$PSQL" -h localhost -p 5432 -U postgres -d bookshelf_test \
  -v ON_ERROR_STOP=1 --single-transaction \
  -f src/database/migrations/001_book_shelf_schema.sql
```

Skip creation and schema setup if the test database and tables already exist.
Run the tests with a database override that leaves `.env` unchanged:

```bash
DB_NAME=bookshelf_test python -m pytest tests/test_repositories.py -v
```

## Development history

Development followed an iterative process:

Research → choose an approach → implement a component → test manually → integrate with the next stage.

See [Development stages](docs/development_stages.md) for the project’s progression and implementation details.

## Project structure

```text

├── src/                                  # Application code
│   │
│   ├── cli.py                            # Parses terminal arguments and runs the pipeline
│   ├── config.py                         # Loads provider settings and creates the OpenRouter client
│   │
│   ├── integrations/                     # External provider clients and detection models
│   │   ├── open_library_client.py        # Searches, matches, and retrieves Open Library metadata
│   │   ├── openrouter_client.py          # Identifies readable books in bookshelf images
│   │   └── detection_schemas.py          # Defines Pydantic models for detection output
│   │
│   ├── services/                         # Coordinates application workflows
│   │   ├── metadata_service.py           # Combines detection and metadata lookup with status counts
│   │   ├── recommendation_service.py     # Combines profile preparation, embeddings, and ranking
│   │   └── bookshelf_pipeline.py         # Coordinates scanning, database storage, and recommendations
│   │
│   ├── ml/                               # Content-based recommendation components
│   │   ├── preprocessing.py              # Validates inputs and prepares book text profiles
│   │   ├── embeddings.py                 # Generates normalized semantic embeddings
│   │   └── ranking.py                    # Calculates similarity and ranks books
│   │
│   ├── database/                         # PostgreSQL connections, schema, and data access
│   │   ├── connection.py                 # Opens connections using environment settings
│   │   ├── migrations/
│   │   │   └── 001_book_shelf_schema.sql  # Creates tables and their foreign keys
│   │   └── repositories/
│   │       ├── scan_repository.py        # Saves and retrieves scan records
│   │       ├── book_repository.py        # Saves and retrieves book metadata
│   │       └── recommendation_repository.py # Saves and retrieves recommendation results
│   │
│   └── api/                              # FastAPI application and HTTP endpoints
│       ├── main.py                       # Creates the app and registers route modules
│       ├── schemas.py                    # Defines and validates API request models
│       └── routes/
│           ├── scans.py                  # Creates and retrieves scan records
│           ├── books.py                  # Retrieves books and books belonging to a scan
│           └── recommendations.py        # Generates, saves, and retrieves recommendations
│   
├── tests/
│   └── test_repositories.py              # Integration tests using PostgreSQL
├── data/
│   ├── book_*.jpg                        # Sample bookshelf photos, numbered 1 through 11
│   └── processed/
│       └── books_metadata.json           # JSON output from the standalone metadata example
│   
├── docs/
│   ├── development_stages.md             # Implementation stages and design decisions
│   └── manual_api_integration_testing.md # Manual checks for the CLI, database, and API
│   
├── .env                                  # Local credentials and configuration
├── .env.example                          # Configuration template without real credentials
├── .gitignore                            # Git ignore rules
├── requirements.txt                      # Python dependencies
└── README.md                             # Project overview and usage
```

The CLI pipeline saves scans, matched books, and recommendations to PostgreSQL.
The JSON file in `data/processed/` is output from the standalone metadata example;
it is not required by the CLI pipeline.
