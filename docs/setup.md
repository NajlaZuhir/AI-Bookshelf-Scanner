# Setup and usage

## First-time setup

The commands below use Git Bash on Windows. Install Conda, PostgreSQL, and
Node.js with npm first, and keep PostgreSQL running. Start from the
`ai-bookshelf-scanner/` project root, which contains `requirements.txt`, `src/`,
and `frontend/`. Commands that change directories are shown explicitly.

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

Skip `CREATE DATABASE` if the database exists. The schema uses
`CREATE TABLE IF NOT EXISTS`, so it can be rerun to create missing tables,
including the metadata cache. It does not modify existing table definitions.

### 5. Start the backend

```bash
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal running. The API documentation is available at
[Swagger UI](http://127.0.0.1:8000/docs).

### 6. Start the frontend

In a second terminal, starting from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the Local URL printed by Vite, normally
[http://localhost:5173/](http://localhost:5173/). Keep both terminals running.
Upload a JPEG/PNG bookshelf photo (up to 10 MB and 20 megapixels), review the
detected books, enter reading preferences, and request recommendations.

Vite forwards `/api` requests to FastAPI on port 8000. Photos are stored in
`data/uploads/`; scans, matched books, and generated recommendations are saved
in PostgreSQL. Uploading a photo alone does not generate a recommendation.

## Running the project again

Keep PostgreSQL running. In the backend terminal, start from the project root:

```bash
conda activate bookshelf
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, starting from the project root:

```bash
cd frontend
npm run dev
```

Database setup is only needed initially. Repeat dependency installation when
setting up a new environment or after dependency changes.

## Optional: run the CLI

From the project root, with the Python environment activated:

```bash
python -m src.cli \
  --image "data/book_1.jpg" \
  --preference "I enjoy science fiction and fantasy" \
  --top-k 3
```

Each CLI run saves a scan, matched books, and an initial recommendation result.
The CLI can be used independently of the frontend and API server.

## Scan rate limiting

SlowAPI limits `POST /scans` per client IP. Configure it in `.env`:

```dotenv
SCAN_RATE_LIMIT=3/minute;20/hour
```

Restart the backend after changing the setting. Exceeding either limit returns
`429` with a `Retry-After` header and this message, which the frontend displays:

```text
Scan limit reached. Please wait before trying again.
```

The limit is checked before the scan endpoint's image processing and external
API calls. Attempts that reach the endpoint count even if image validation
fails. CLI scans run directly and bypass HTTP rate limiting.

Counters are stored in memory for one backend process and reset when it
restarts or reloads. Local requests normally share the localhost IP quota.
Multiple workers or servers require shared counter storage, such as Redis;
deployment behind a proxy also requires trusted forwarding of client IPs.

The minute limit was manually verified; the configured hourly limit was not
separately tested. See the [manual check](manual_api_integration_testing.md#optional-verify-scan-rate-limiting).

## Troubleshooting

`ECONNREFUSED 127.0.0.1:8000` in the Vite terminal means the frontend cannot reach
FastAPI. Start the backend on port 8000 and keep both terminals running. If the
backend exits, check its terminal for the startup error.

## Optional: Google Vision fallback

The fallback is disabled by default. To enable it:

1. Create or select a Google Cloud project, enable billing, and enable the
   Cloud Vision API. Follow [Google's setup guide](https://docs.cloud.google.com/vision/docs/setup).
2. Install the Python dependency in the environment used to run this project:

   ```bash
   python -m pip install google-cloud-vision
   ```

3. Install the Google Cloud CLI and configure local Application Default
   Credentials. Replace `YOUR_PROJECT_ID` with your project ID:

   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project YOUR_PROJECT_ID
   ```

4. Set `GOOGLE_VISION_FALLBACK_ENABLED=true` in `.env`, then restart the backend
   or CLI process. Set it to `false` to disable the fallback.

See [Google's authentication guide](https://docs.cloud.google.com/vision/docs/authentication).
The Google SDK and credentials are initialized only if fallback is needed.

OpenRouter remains the primary provider. An API failure or invalid structured
response triggers Google Vision; a valid empty book list does not. If both
providers fail, processing reports an error instead of an empty successful scan.

Google Vision OCR paragraphs become candidate titles with unknown authors,
then pass through the existing cached Open Library matching. Duplicate matched
work IDs are removed. This is a best-effort fallback: OCR paragraphs may split
or combine text from different books. Its detected count represents text
candidates, not confirmed books. CLI/backend messages identify the provider,
and scan responses include `detection_source`.

## Optional: run repository tests

See the [integration testing guide](manual_api_integration_testing.md#repository-tests)
for test database setup and the pytest command. The same guide documents manual
image-upload, retrieval, and recommendation checks.
