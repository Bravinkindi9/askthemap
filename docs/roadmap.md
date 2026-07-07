# AskTheMap Roadmap

## V1 — MVP

- [x] Project scaffold and documentation
- [x] FastAPI backend with health endpoint
- [x] Geo module: STAC search + image retrieval from Planetary Computer
- [x] VLM integration: provider-agnostic layer with Gemini
- [x] Query endpoint: geo + VLM pipeline
- [x] Next.js frontend with Leaflet map
- [x] End-to-end flow: click → question → answer
- [x] Basic test suite
- [x] CI/CD pipeline
- [ ] Deployment

## V2 — Milestone 1: Trust & Explainability (Current)

- [x] Structured VLM output (summary, detail, confidence, caveats, supporting evidence)
- [x] Return the exact analyzed satellite tile so users can visually verify the answer
- [x] Enriched image metadata (platform, instrument, resolution) alongside date/cloud cover
- [x] Real timeouts + graceful, user-safe error handling on every external call
- [x] Regression coverage for the raster window edge-clamping bug
- [x] Staged loading feedback in the UI (capped, never overclaims progress)
- [ ] Deployment path (Dockerfile, prod ASGI config, per-environment CORS)

## Future Considerations

- Backend-driven progress streaming (replace the simulated staged loading with
  real per-stage events once there's a caching/job-queue layer to build it on)
- Per-location result caching
- Auto-generate the TS client from the FastAPI OpenAPI schema
- Test coverage for `packages/geo`'s STAC search path (no-results, network failure)
- Region highlighting / bounding-box grounding for supporting evidence
- Support additional VLM providers (Claude, GPT-4o) — the abstraction already exists
- Time-series analysis (compare imagery across dates)
- Rate limiting on `/api/query`
- Multi-language support
