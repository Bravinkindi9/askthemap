# AskTheMap Architecture

## System Flow

```
User (Browser)
     │
     ▼
┌──────────┐     POST /api/query
│  Next.js │ ──────────────────────►  ┌──────────────┐
│  Web App │                          │  FastAPI API  │
│  :3000   │ ◄──────────────────────  │  :8000       │
└──────────┘     QueryResponse        └──────┬───────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                        ┌──────────┐  ┌──────────┐  ┌──────────┐
                        │   STAC   │  │   Image  │  │   VLM    │
                        │  Search  │  │  Fetch   │  │  Layer   │
                        └────┬─────┘  └────┬─────┘  └────┬─────┘
                             │             │              │
                             ▼             ▼              ▼
                        Planetary    Sentinel-2       Gemini
                        Computer     COG tiles        Vision
```

## Components

### Frontend (`apps/web/`)
- Next.js + TypeScript
- Leaflet map with OpenStreetMap tiles
- Click-to-select coordinate, question input, answer display

### API (`apps/api/`)
- FastAPI with Pydantic models
- Routes: `/health`, `/api/query`
- VLM abstraction layer (`app/vlm/`) — provider-agnostic interface
- Configuration via environment variables (prefix: `ATM_`)

### Geo Module (`packages/geo/`)
- `stac_search.py` — searches Planetary Computer STAC for Sentinel-2 L2A
- `image_retrieval.py` — windowed COG reads via rasterio, returns PIL Image

### VLM Layer (`apps/api/app/vlm/`)
- `base.py` — abstract `BaseVLM` with `ask(image, question, lat, lon)` interface
- `gemini.py` — Google Gemini implementation (default)
- Swap providers by adding a new implementation and changing the factory in `__init__.py`

## Data Flow for a Query

1. User clicks map → frontend captures (lat, lon)
2. User types question → frontend sends `POST /api/query`
3. API searches STAC catalog for recent low-cloud Sentinel-2 imagery
4. API downloads a 512x512 px tile from the COG centered on the coordinate
5. API sends image + question + location context to Gemini Vision
6. Gemini returns natural language analysis
7. API returns structured response with answer + image metadata
8. Frontend displays the answer
