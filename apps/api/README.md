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

### Switching VLM providers

`get_vlm()` (`app/vlm/__init__.py`) returns whichever provider `ATM_VLM_PROVIDER` selects —
switching is a config change only, nothing else in the codebase (routes, models,
frontend) needs to change:

```bash
ATM_VLM_PROVIDER=gemini       # default — needs ATM_GEMINI_API_KEY
ATM_VLM_PROVIDER=openrouter   # needs ATM_OPENROUTER_API_KEY
```

OpenRouter gives free access to several open vision-language models (no card
required) — get a key at [openrouter.ai/keys](https://openrouter.ai/keys) and
set `ATM_OPENROUTER_MODEL` to any vision-capable `:free` model slug (defaults to
`qwen/qwen2.5-vl-7b-instruct:free`). To add another provider later, implement
`BaseVLM` in `app/vlm/` and add one branch to `get_vlm()`.

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
