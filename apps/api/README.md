# AskTheMap API

Python FastAPI backend that handles geospatial queries — searches satellite imagery, retrieves image tiles, and sends them to a Vision Language Model for analysis.

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
# Edit .env and set ATM_GEMINI_API_KEY
```

## Run

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

## Endpoints

- `GET /health` — health check
- `POST /api/query` — main query endpoint

### POST /api/query

```json
{
  "lat": -1.9403,
  "lon": 29.8739,
  "question": "What type of development is happening here?"
}
```

Returns:

```json
{
  "lat": -1.9403,
  "lon": 29.8739,
  "question": "...",
  "analysis": {
    "summary": "...",
    "detail": "...",
    "confidence": "medium",
    "caveats": ["..."],
    "supporting_evidence": ["..."]
  },
  "image_metadata": {
    "datetime": "2026-06-12T08:10:21Z",
    "cloud_cover": 28.1,
    "collection": "sentinel-2-l2a",
    "asset_href": "...",
    "platform": "Sentinel-2B",
    "instrument": "msi",
    "resolution_m": 10.0
  },
  "image_base64": "..."
}
```

`image_base64` is the exact PNG tile that was sent to the VLM, base64-encoded
with no `data:` prefix — prepend `data:image/png;base64,` client-side to render it.

On failure, the endpoint returns a specific status with a user-safe `detail`
message (never the raw exception): `404` if no recent cloud-free imagery is
available, `503` if the VLM API key isn't configured, `504` if a stage (STAC
search, image download, or the VLM call) exceeded its timeout, `502` for any
other upstream failure. Per-stage timeouts are configurable via
`ATM_STAC_TIMEOUT_S`, `ATM_IMAGE_FETCH_TIMEOUT_S`, `ATM_VLM_TIMEOUT_S`.
