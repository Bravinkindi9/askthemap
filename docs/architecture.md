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
- Click-to-select coordinate, question input, structured analysis panel with the
  analyzed satellite tile, confidence badge, supporting evidence, and caveats

### API (`apps/api/`)
- FastAPI with Pydantic models
- Routes: `/health`, `/api/query`
- VLM abstraction layer (`app/vlm/`) — provider-agnostic interface
- Configuration via environment variables (prefix: `ATM_`), including per-stage timeouts

### Geo Module (`packages/geo/`)
- `stac_search.py` — searches Planetary Computer STAC for Sentinel-2 L2A, returns
  imagery metadata (datetime, cloud cover, platform, instrument, resolution)
- `image_retrieval.py` — windowed COG reads via rasterio, returns PIL Image; the
  crop window is clamped to the raster bounds on all sides so a point near a tile
  edge still returns a full-size, undistorted crop

### VLM Layer (`apps/api/app/vlm/`)
- `base.py` — abstract `BaseVLM` with `ask(image, question, lat, lon) -> AnalysisResult`
- `schemas.py` — `AnalysisResult` (summary, detail, confidence, caveats, supporting
  evidence) and `Confidence` (low/medium/high). Owned by the VLM layer, not the API
  layer, so it stays meaningful independent of how the API exposes it.
- `gemini.py` — Google Gemini implementation using structured JSON output
  (`response_schema=AnalysisResult`), so the model's response is validated into
  the schema directly rather than parsed from free text
- Swap providers by adding a new implementation and changing the factory in `__init__.py`

## Data Flow for a Query

1. User clicks map → frontend captures (lat, lon)
2. User types question → frontend sends `POST /api/query`
3. API searches STAC catalog for recent low-cloud Sentinel-2 imagery (bounded by
   `stac_timeout_s`)
4. API downloads a 512x512 px tile from the COG centered on the coordinate
   (bounded by `image_fetch_timeout_s`)
5. API sends image + question + location context to Gemini Vision, requesting a
   structured `AnalysisResult` (bounded by `vlm_timeout_s`)
6. API returns `QueryResponse`: the structured analysis, enriched image metadata,
   and the exact analyzed tile as a base64-encoded PNG
7. Frontend renders the tile, confidence badge, summary/detail, evidence, and
   caveats — so the user can visually verify what the AI is describing

Each stage's external call is failure-isolated: a timeout or upstream error at any
stage returns a specific, user-safe HTTP error (404 for no imagery, 504 for a stage
that timed out, 502 for an upstream failure) with the underlying exception logged
server-side only. See ADR 007.
