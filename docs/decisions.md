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

## ADR 006: Structured VLM output, returned inline with the image

Decision:
`BaseVLM.ask()` returns an `AnalysisResult` (summary, detail, confidence, caveats,
supporting evidence) instead of a free-text string, produced via Gemini's native
structured JSON output (`response_schema`) rather than a second parsing pass. The
`QueryResponse` also returns the exact analyzed satellite tile, base64-encoded
inline in the same JSON payload, plus enriched STAC metadata (platform, instrument,
resolution).

Reason:
A free-text answer gives the user no way to judge how much to trust it, and no way
to verify it against what the AI actually saw. Structured output makes confidence
and caveats first-class instead of buried in prose, and returning the image lets
the user visually check the claim against the source data. `AnalysisResult` lives
in the VLM layer (`app/vlm/schemas.py`), not the API layer, so the contract stays
owned by "what a VLM returns" rather than "what this endpoint returns" — a future
provider or a non-HTTP consumer can reuse it unchanged.

Returning the image inline as base64 (rather than a separate image endpoint) was a
deliberate scope decision: it keeps the API stateless with a single round trip,
which is right while there is one frontend consumer and no caching layer yet. If a
caching or image-history feature is added later, moving to a separate image
resource is a natural, self-contained follow-up — it doesn't require reworking
this schema.

This is a breaking change to `QueryResponse` (`answer: str` → `analysis:
AnalysisResult`; `image_metadata` becomes required; `image_base64` added). Applied
in place rather than versioned, since the only consumer is this repo's own
frontend.

Date:
July 2026

## ADR 007: Two-layer timeout policy for external calls

Decision:
Every external call (STAC search, COG read, Gemini call) is bounded twice: once at
the underlying client (`pystac_client`'s `timeout`, GDAL's `GDAL_HTTP_TIMEOUT` /
`GDAL_HTTP_CONNECTTIMEOUT`, Gemini's `http_options.timeout`), and again by
`asyncio.wait_for` at the call site in `query.py`. Failures are mapped to a small,
fixed set of user-safe HTTP responses (404 no imagery, 504 stage timeout, 502
upstream failure); the real exception is logged server-side only and never appears
in the response body.

Reason:
`asyncio.wait_for` around a `asyncio.to_thread`-bridged blocking call (rasterio/GDAL,
`requests`) bounds how long the API *waits*, but cannot cancel the underlying call —
the background thread keeps running until the library's own timeout fires. Relying
on `wait_for` alone would let threads pile up under repeated timeouts without
actually freeing the stalled resource. The library-level timeout is the real
defense; `wait_for` is the user-facing backstop guaranteeing a bounded response time
even if a library-level timeout is misconfigured or doesn't apply to every request
a stage makes internally.

Default timeout values were calibrated against real Planetary Computer / Azure Blob
latency observed during development (STAC search ~11s, windowed COG read ~37s on a
typical residential connection) — they're set with headroom above a single
request's measured cost, not tuned to the theoretical minimum, and are configurable
via `ATM_STAC_TIMEOUT_S`, `ATM_IMAGE_FETCH_TIMEOUT_S`, `ATM_VLM_TIMEOUT_S` since
this cost is highly network-dependent.

Date:
July 2026
