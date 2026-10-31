# Setup and usage

## First-time setup

The commands below use Git Bash on Windows. Install Conda and PostgreSQL first,
and make sure the PostgreSQL server is running. Run all commands from the
`ai-bookshelf-scanner/` project root, which contains `requirements.txt` and `src/`.

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
See the [manual integration guide](manual_api_integration_testing.md) to
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
