# Shelf Scanner frontend

A React + Vite interface for the existing FastAPI backend.

## Run locally

Activate your Python environment and start the backend from `ai-bookshelf-scanner`:

```powershell
python -m uvicorn src.api.main:app --reload
```

In another terminal, from this `frontend` directory:

```powershell
npm install
npm run dev
```

Open the Local URL printed by Vite. The backend needs its normal PostgreSQL and
OpenRouter configuration. Uploading a photo calls the real backend services.

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

## Build

```powershell
npm run build
```

The production files are generated in `dist/`. The font stylesheet uses Google
Fonts, with local serif and sans-serif fallbacks when offline.
