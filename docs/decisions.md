# Technical Decisions

## ADR 001: Project foundation

Decision:
Build AskTheMap as a full-stack application with separate frontend and backend.

Reason:
This allows the system to grow beyond a prototype.

Date:
June 2026

## ADR 002: Technology stack

Decision:
- Backend: Python + FastAPI
- Frontend: Next.js + TypeScript
- Maps: Leaflet + OpenStreetMap
- Satellite data: Microsoft Planetary Computer (Sentinel-2 L2A via STAC)
- AI: Google Gemini (with provider-agnostic abstraction)

Reason:
Python is the standard for geospatial work (rasterio, pystac-client). Next.js provides a modern frontend with good DX. Leaflet + OSM avoids API key requirements. Planetary Computer provides free, open satellite data. Gemini offers strong vision capabilities with a generous free tier.

Date:
June 2026

## ADR 003: VLM abstraction

Decision:
Create an abstract base class `BaseVLM` with a single `ask()` method. Each provider implements this interface. A factory function returns the active provider.

Reason:
The AI model market changes fast. Coupling the entire app to one provider creates lock-in. The abstraction is minimal (one method) so it adds almost no complexity while making provider swaps trivial.

Date:
June 2026

## ADR 004: Geo module as sys.path import

Decision:
`packages/geo` is imported by the API via `sys.path` manipulation, not as an installed pip package.

Reason:
Avoids packaging complexity for V1. The geo module has no independent consumers — only the API uses it. If the project grows to need multiple consumers, we can convert it to a proper package later.

Date:
June 2026

## ADR 005: Environment variable prefix

Decision:
All environment variables use the `ATM_` prefix (e.g., `ATM_GEMINI_API_KEY`).

Reason:
Avoids collision with other tools and makes it clear which variables belong to AskTheMap.

Date:
June 2026
