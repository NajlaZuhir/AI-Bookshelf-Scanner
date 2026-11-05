# Shelf Scanner frontend

A React + Vite interface for the existing FastAPI backend.

## Run locally

Activate your Python environment and start the backend from `ai-bookshelf-scanner`:

```powershell
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, from this `frontend` directory:

```powershell
npm install
npm run dev
```

Open the Local URL printed by Vite, normally
[http://localhost:5173/](http://localhost:5173/). Keep both terminals and
PostgreSQL running. The backend needs its normal PostgreSQL and OpenRouter
configuration; see the [project setup guide](../docs/setup.md). Uploading a
photo calls the real backend services. After initial setup, run `npm install`
again when dependencies change.

## Workflow

1. Choose or drop a JPEG/PNG photo (up to 10 MB and 20 megapixels).
2. Scan the bookshelf and review detected titles and metadata lookup statuses.
3. Enter reading interests and request up to three recommendations.

Changing the photo clears the previous scan and recommendations. Unmatched
titles remain visible in the scan response, while recommendations use matched
books. Empty results and request failures are displayed in the interface.

## API connection

The frontend sends multipart data with a `file` field to `/api/scans`, then sends
JSON with `preference_text` and `top_k` to
`/api/scans/{scan_id}/recommendations`. Vite's development proxy strips `/api`
and forwards requests to `http://127.0.0.1:8000`.

For hosting, configure the web server to route `/api/*` to FastAPI, stripping
the prefix, or adapt `src/api.js` to a deployed backend URL with appropriate CORS.
Vite's proxy applies to the development server only.

## Troubleshooting

`ECONNREFUSED 127.0.0.1:8000` in the Vite terminal means the frontend cannot reach
the backend. Start FastAPI on port 8000 and keep its terminal running alongside
Vite. Check [Swagger UI](http://127.0.0.1:8000/docs) to confirm it is available;
if it fails to start, inspect the backend terminal error.

## Build

```powershell
npm run build
```

The production files are generated in `dist/`. The font stylesheet uses Google
Fonts, with local serif and sans-serif fallbacks when offline.
