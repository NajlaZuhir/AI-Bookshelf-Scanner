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

Copy `.env.example` to `.env` and fill in your OpenRouter API key and PostgreSQL
credentials. Keep your existing `.env` if already configured.

```bash
cp .env.example .env
```

### 4. Set up the database

Use your database details from `.env` and adjust the PostgreSQL executable path:

```bash
PSQL="/c/Program Files/PostgreSQL/18/bin/psql.exe"

"$PSQL" -h localhost -p 5432 -U postgres -d postgres \
  -v ON_ERROR_STOP=1 -c "CREATE DATABASE book_shelf;"

"$PSQL" -h localhost -p 5432 -U postgres -d book_shelf \
  -v ON_ERROR_STOP=1 --single-transaction \
  -f src/database/migrations/001_book_shelf_schema.sql
```

Run once. Skip `CREATE DATABASE` if the database exists; skip the migration if
its tables already exist.

### 5. Run the application

```bash
python -m src.cli \
  --image "data/book_1.jpg" \
  --preference "I enjoy science fiction and fantasy" \
  --top-k 3
```

The CLI saves matched books and recommendations to PostgreSQL.

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

See the [integration testing guide](manual_api_integration_testing.md#repository-tests)
for test database setup and the pytest command.
