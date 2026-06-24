# AskTheMap

Ask any question about any point on Earth and get an answer grounded in satellite imagery.

## Problem

Understanding places on Earth usually requires GIS skills, expensive tools, or technical knowledge.

AskTheMap makes geospatial intelligence accessible through natural language.

## How It Works

1. Open the web app and see a world map
2. Click any location on Earth
3. Type a question (e.g., "What type of development is happening here?")
4. The system retrieves recent Sentinel-2 satellite imagery for that location
5. A Vision Language Model analyzes the imagery and answers your question

## Tech Stack

- **Frontend:** Next.js + TypeScript + Leaflet
- **Backend:** Python + FastAPI
- **Satellite Data:** Microsoft Planetary Computer (Sentinel-2 L2A via STAC)
- **AI:** Google Gemini Vision (provider-swappable)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env and set ATM_GEMINI_API_KEY

python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

## Project Structure

```
askthemap/
  apps/
    api/          Python FastAPI backend
    web/          Next.js frontend
  packages/
    geo/          Satellite imagery search and retrieval
  tests/          Test suite
  docs/           Architecture, decisions, roadmap
  scripts/        Development utilities
```

## Documentation

- [Architecture](docs/architecture.md)
- [Technical Decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)

## Status

In development — V1 MVP.

## Creator

Brave Inkindi
