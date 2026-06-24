\# AskTheMap Build Journal



\## Day 1

Started building AskTheMap.

Goal:
Move from learning about technology to building and shipping a real GeoAI system.

Today:
\- created GitHub repository
\- initialized local project
\- created project documentation

Next:
Define technical architecture and start development.


\## Day 2

Built the complete V1 application from scaffold to working product.

Decisions:
\- Python FastAPI for backend
\- Next.js + TypeScript for frontend
\- Leaflet + OpenStreetMap for maps (no API key needed)
\- Microsoft Planetary Computer for satellite imagery (Sentinel-2 L2A via STAC)
\- Google Gemini for Vision Language Model (with provider-agnostic abstraction)

Built:
\- FastAPI backend with health endpoint and query endpoint
\- Geo module: STAC search + COG image retrieval from Planetary Computer
\- VLM integration layer with abstract base class and Gemini implementation
\- Next.js frontend with Leaflet map, click-to-select, question input, answer display
\- Test suite (9 tests passing)
\- CI workflow for GitHub Actions
\- Full documentation: architecture, decisions, roadmap, READMEs

Verified:
\- STAC search returns Sentinel-2 imagery for Kigali (-1.9403, 29.8739)
\- Health endpoint returns 200
\- All tests pass
\- Frontend builds successfully

Next:
\- Test end-to-end with a real Gemini API key
\- Deploy
