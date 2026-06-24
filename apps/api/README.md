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
  "answer": "...",
  "lat": -1.9403,
  "lon": 29.8739,
  "question": "...",
  "image_metadata": {
    "datetime": "2026-06-12T08:10:21Z",
    "cloud_cover": 28.1,
    "collection": "sentinel-2-l2a",
    "asset_href": "..."
  }
}
```
