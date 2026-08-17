# Askio V1 — Technical Audit

**Audit date:** 17 August 2026  
**Scope:** Read-only repository audit. No application code, dependency, configuration, or deployment change was made.

## Executive Verdict

Askio is a promising, unusually well-scoped prototype with a real end-to-end path: map point → recent Sentinel-2 image → VLM answer → inspected source image. The Python/TypeScript split, small VLM interface, typed contracts, error isolation, and test coverage are good foundations.

It is not yet a credible *geospatial question-answering system*: it is principally a **single-image VLM demo**. It sends a 512×512 RGB Sentinel-2 crop (normally 10 m pixels, roughly 5.12 km wide) and a question to a general vision model, then presents the model's claimed observations as “supporting evidence.” Those strings are interpretations, not independently computed facts.

The application also has one immediate availability failure: its default `gemini-2.0-flash` model was shut down on 1 June 2026. A valid key cannot make that model work. The local Gemini secret is correctly kept out of the browser and ignored by Git, but the unauthenticated expensive endpoint has no rate limiting, and it returns a signed Planetary Computer asset URL to every caller.

**Recommendation:** keep the current monolith and map stack, but make the V1 evidence-first. Use deterministic geospatial measurements for a small, explicit question set; use an optional local/hosted VLM only to explain those measurements and visible context. Deploy the static frontend freely; run the full Python/raster pipeline locally for development and demos until there is a genuinely suitable free Python runtime. Do not migrate to microservices, a database, cloud queues, or a new frontend framework.

## 1. What Askio V1 Currently Is

Askio (still named `AskTheMap` throughout the code and UI) is a two-process web application:

- A Next.js 15 / React 19 client displays an OpenStreetMap/Leaflet map, takes a clicked latitude/longitude and free-text question, then shows one returned image and analysis.
- A FastAPI service validates the request, searches Microsoft Planetary Computer's public STAC endpoint for the newest Sentinel-2 L2A scene under 30% scene cloud cover in the last 180 days, reads a 512 px RGB window from its visual COG, and sends PNG bytes plus the question to Gemini or OpenRouter.

It has no accounts, database, persistent history, cache, geocoder, true spatial analysis, time-series comparison, or server-side job system. That is sensible V1 scope.

## 2. Current Architecture

```text
Browser
  └─ Next.js client (Leaflet + public OSM tiles)
       └─ POST {lat, lon, question} to FastAPI /api/query
            ├─ PySTAC Client + Planetary Computer signing
            │    └─ newest Sentinel-2 L2A STAC item (≤30% scene cloud, 180 days)
            ├─ rasterio/GDAL range-read
            │    └─ 512×512 visual RGB COG crop
            ├─ GeminiVLM or OpenRouterVLM
            │    └─ structured AnalysisResult JSON
            └─ QueryResponse
                 └─ analysis + STAC metadata + base64 PNG
       └─ analysis panel / tile preview
```

| Component | Responsibility / I/O | External dependency and auth | Failure / assessment |
| --- | --- | --- | --- |
| `apps/web` | Input point/question; renders response. | OSM public raster tiles; API URL exposed by design. No key. | Tile availability/usage policy; mobile layout is basic. Necessary. |
| `app/routers/query.py` | Orchestrates request stages and maps failures to 404/502/504. | Planetary Computer, selected VLM. | Sequential latency can exceed 95 s; no rate limit/cache. Necessary. |
| `packages/geo/stac_search.py` | Point/intersects STAC search, newest qualifying scene. | Public STAC; anonymous SAS signing for COGs. | No image from last 180 days, throttling, stale token. Necessary but too thin as evidence. |
| `packages/geo/image_retrieval.py` | Reprojects point, window-reads RGB COG, clips/stretchs values. | GDAL/rasterio + signed Azure blob URL. | Slow remote reads; scene edges shift crop away from clicked point. Necessary for image experience. |
| `app/vlm/*` | Provider swap plus schema. Takes image/question/location, produces prose. | Gemini key or OpenRouter bearer key. | Quota/model availability/invalid JSON/upstream failure. Useful, not authoritative. |
| Response | Returns image, metadata and prose. | None. | Base64 overhead; exposes signed `asset_href`. Needs adjustment. |

The VLM abstraction is appropriately small: one `ask()` method. The `sys.path` import for `packages/geo` is pragmatic today, though packaging it or moving it under the API later would remove a fragile runtime assumption.

## 3. Gemini/VLM Investigation

### What Gemini does

`GeminiVLM.ask()` serializes the fetched PIL crop as PNG, adds the coordinate/question prompt, and calls `google.genai.Client.models.generate_content()` with JSON schema output. Gemini is asked to identify visible land cover, urban areas, water, infrastructure and terrain; to produce `summary`, `detail`, confidence, caveats and “supporting evidence.” It receives **one satellite image and text**, not raw multispectral bands, vector data, a time series, or computed GIS statistics.

The configured model is `gemini-2.0-flash`. Google confirms this model was shut down on **1 June 2026**; its current deprecation guidance names a newer Flash replacement. This is a code/configuration defect, not a key diagnosis. [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)

### What works without Gemini

The frontend map, point selection, typed API, STAC search, signed COG retrieval, crop production, metadata extraction, health endpoint and tests still work. The current `/api/query` endpoint deliberately stops with 503 before returning a tile if no active VLM key exists, so the usable user flow does **not** work without a provider until it is changed to support an evidence-only result.

### Necessity classification

**Useful but replaceable; currently architecturally over-relied upon.** A VLM is valuable for flexible natural-language explanation and visual context, but it is not necessary for “nearest road,” land-cover class, NDVI, built-up proportion, distance to water, or change statistics. A 10 m RGB image is also insufficient for confident claims about many residential-scale features. VLM prose should never be Askio's only evidence layer.

### Key/API/configuration

- The server loads `ATM_GEMINI_API_KEY` / `ATM_OPENROUTER_API_KEY` from `apps/api/.env` using the `ATM_` prefix. The key is not shipped to the Next.js bundle; only `NEXT_PUBLIC_API_URL` is public.
- Gemini uses the current Google Gen AI SDK (`google-genai`), not the old `google-generativeai` SDK. Its SDK choice is sound; its default model identifier is obsolete.
- Gemini free access exists but is account-, model-, region- and quota-dependent. Limits are per project, not per key, and vary by model/tier. Inspect the actual project limits in AI Studio rather than infer them from a key. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- OpenRouter uses an OpenAI-compatible endpoint and a hard-coded `qwen/qwen2.5-vl-7b-instruct:free` default. Free model IDs/availability are volatile. Current OpenRouter documentation says non-credit accounts are limited to 50 free requests/day and free models are not production reliable. [OpenRouter FAQ](https://openrouter.ai/docs/faq)
- An invalid `ATM_VLM_PROVIDER` silently selects Gemini while the key precheck also treats it as Gemini. Configuration should eventually use a literal enum and fail at startup.

### Security conclusion

The VLM keys are not browser-exposed in this repository, which is correct. Keep that boundary. Do not put any provider key in `NEXT_PUBLIC_*`, a client component, or a static site. The correct shape is browser → your server → provider, with the provider secret stored only in the server host's secret store.

## 4. Major Problems

| Severity | Problem | Smallest fix | Fix now? |
| --- | --- | --- | --- |
| Critical | Default Gemini model is retired. | Change to an actually available model after a real account test, or make evidence-only mode first-class. | **Yes** |
| High | VLM is treated as source of geographic “evidence.” | Return computed evidence separately; label model prose interpretation. | **Yes** |
| High | Unauthenticated endpoint triggers paid/quota-limited inference and remote reads. | Add IP-based rate limiting, request-size limits and a small cache. | **Before public deploy** |
| High | `asset_href` contains a temporary SAS read token and is returned to clients. | Do not return it; return item ID/collection/source URL without credentials. | **Yes** |
| High | Newest scene + scene-wide cloud threshold does not prove the crop is clear or suitable. | Pixel/cloud check where available; inspect/signal crop quality; expose acquisition date. | **Yes** |
| Medium | A crop at scene boundary is clamped and may no longer be centered on the selected point. | Return actual crop bounds/centre; reject or explicitly label shifted windows. | Soon |
| Medium | 10 m RGB can not support fine-grained claims. | Constrain question templates and confidence; add evidence metrics. | Yes |
| Medium | 95 seconds of sequential timeout budget is a poor interactive experience. | Cache search/render; offer evidence as soon as available; lower UI expectations. | Soon |
| Medium | Product, UI, metadata and repository still use AskTheMap. | Intentional rename sweep after audit. | Soon |

## 5. Critical Security Issues

1. **Signed asset URL disclosure — High.** Planetary Computer's signing modifier adds a SAS token to the asset HREF. The response returns that full HREF, allowing any recipient to use it until expiry. It is a temporary read credential, not a harmless metadata URL. Return a STAC item ID and normal source attribution instead. Planetary Computer documents that these asset tokens expire and grant data read access. [SAS token documentation](https://planetarycomputer.microsoft.com/docs/concepts/sas/)
2. **Inference/API abuse — High before public exposure.** No auth is appropriate for a personal demo, but no rate limit is not. An attacker can consume a free quota, trigger costly future requests, and exhaust GDAL threads. Add a conservative edge/server limit, maximum body size, per-IP concurrency cap and cache; do not build accounts merely for this.
3. **Prompt injection — Medium.** The raw user question is appended into the analyst instruction. A question can instruct the VLM to ignore its task or fabricate output. It cannot access server secrets through this prompt, but it can corrupt the result. Delimit quoted user input and make the schema/evidence layer authoritative.
4. **Input/operational controls — Medium.** Coordinates and question length are validated well. Missing: provider enum validation, response body/analysis length bounds, origin-specific production CORS configuration, and structured request IDs/log redaction policy. CORS presently defaults to localhost with credentials disabled, which is reasonable locally.
5. **Secret history — audited.** `.env` and `.env.local` are ignored and neither was found tracked by Git. A non-placeholder Gemini value exists locally; do not print, commit, or reuse it. Rotate it immediately if it was ever copied into an issue, screenshot, deployment log, or external service.

## 6. AI Alternatives

| Option | $0 reality | Fit | Decision |
| --- | --- | --- | --- |
| Gemini hosted | A constrained free tier, availability/quotas vary; data may be used to improve products on free tier. | Strong structured multimodal analysis when available. | Optional development provider, never sole dependency. |
| OpenRouter `:free` | $0, but 50 requests/day without credits and availability/model IDs can change. | Convenient provider experimentation. | Fine demo fallback, not foundation. |
| Hugging Face hosted inference | Free usage/policy is variable and often queued/limited. | Useful for experiments. | Do not design V1 around it. |
| Ollama / llama.cpp with a small VLM (e.g., Qwen VL family) | No usage bill after download; needs RAM, disk and GPU/CPU patience. | Best privacy/reproducibility for demos on capable laptop. | Preferred optional VLM path. |
| Deterministic GIS | Fully local/open libraries plus open data; compute costs only your machine. | Best for measurable place facts. | Core recommendation. |

For a normal student laptop, a 3–7B quantized VLM may be viable with 16 GB RAM but can be slow on CPU; vision adds memory and latency. Treat local VLM as an optional enhancement, not a deployment requirement. Do not promise a specific model's performance until it is benchmarked on the actual laptop and imagery.

## 7. Recommended Zero-Cost Architecture

### Architecture A — current, cleaned

FastAPI + Next.js + Planetary Computer + one hosted VLM. Fix model configuration, remove signed URL, add rate limit/cache, and make provider errors explicit.

**Pros:** least code; keeps image Q&A. **Cons:** VLM quota fragility and weak evidence. **Cost:** $0 only within external free quotas. **Lock-in:** medium for VLM, low for STAC. **Recommendation:** transitional only.

### Architecture B — zero-cost cloud-first

Static Next.js frontend on Cloudflare Pages/Vercel; thin edge API for request validation/cache; open STAC/vector data; OpenRouter/Gemini free tier for optional interpretation. A Python/rasterio pipeline cannot run inside a 10 ms Workers Free CPU budget, so it must be external or redesigned around remote render APIs.

**Pros:** easy public demo. **Cons:** not truly reliable $0 for Python imagery analysis or VLM; free services change. **Cost:** $0 with hard quotas. **Lock-in:** medium. **Recommendation:** static public shell only, unless features are narrowed to remote HTTP calls.

### Architecture C — local-first (recommended)

Keep this FastAPI app on the student's laptop. Add an `evidence` service/module that uses STAC/rasterio, GeoPandas/Shapely and local cached OSM extracts or Overpass carefully. Compute facts first. Run an optional Ollama/llama.cpp VLM locally; otherwise render a deterministic evidence report. Host only the static frontend when sharing, or demonstrate the complete system locally/video.

**Pros:** genuinely no operating bill, reproducible, privacy-preserving, technically substantive. **Cons:** machine must be on for live demo; remote source latency remains. **Complexity:** low-to-medium; one process and a small cache. **Lock-in:** low. **Recommendation:** choose this.

## 8. Geospatial/Data Architecture

Current data source: **Microsoft Planetary Computer `sentinel-2-l2a`**. It is global, multispectral, revisits frequently, has 10 m visible/NIR bands (with coarser bands too), and is appropriate for regional land-cover/vegetation/large-water questions—not property-level truth. The code uses its prebuilt visual asset, not raw multispectral bands, so it currently cannot calculate NDVI. STAC metadata is public; COG reads use anonymous temporary SAS signing and may be throttled. [Planetary Computer STAC quickstart](https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/)

Use sources only where they answer a concrete question:

| Need | Evidence source / method | Caveat |
| --- | --- | --- |
| Recent natural/urban context | Sentinel-2 L2A RGB + cloud quality; 10 m. | No fine-detail claims. |
| Vegetation | Sentinel-2 B04/B08 → NDVI median/distribution in a defined buffer. | Clouds/shadows, seasonal variation. |
| Surface water | Sentinel-2 B03/B08 → NDWI plus water mask where justified. | Turbid/urban water ambiguity. |
| Nearby roads/buildings/POIs | OpenStreetMap vectors; distance/count/length via Shapely. | Completeness varies; public tile server is not an analysis API. |
| Change | Two or more cloud-screened Sentinel acquisitions, aligned buffer, difference metrics. | Must report dates and uncertainty. |
| Baseline land cover | A named published land-cover product, with its version/date/resolution. | Do not mix classes without documenting method. |

Microsoft Planetary Computer remains a good anonymous V1 source but is a service dependency, not guaranteed infrastructure. Keep a STAC provider URL/configuration boundary so Copernicus Data Space, USGS Landsat, or another STAC endpoint can replace it. Google Earth Engine is useful for research but adds account/terms/vendor lock-in; do not make it the V1 dependency.

## 9. Truth Layer Proposal

Yes—make this the defining architecture.

```text
Query intent + point/buffer
    ├─ deterministic retrieval / calculation → EvidenceRecord (facts, units, dates, methods, sources, quality)
    └─ optional VLM → Interpretation (only receives EvidenceRecord + image)
                                      ↓
                       Answer UI: evidence first, interpretation second
```

Example `EvidenceRecord`: acquisition date; cloud score; actual crop bounds; buffer radius; NDVI median/IQR; water percentage; building/road counts; source item IDs; calculation version; limitations. The VLM may say “moderately vegetated and urbanized,” but must not invent a percentage, date, distance or source. If a requested metric is unavailable, say “not measured” rather than silently substitute prose.

For “What is surrounding urban development like here?”: validate point → select explicit e.g. 1 km buffer in an appropriate projected CRS → retrieve recent clear Sentinel scene → calculate a small set of measures → optionally retrieve OSM roads/buildings → generate an interpretation constrained to those fields → return image/map overlays, results, dates/sources and limitations. Error sources include coordinate/CRS transformation, scene selection, cloud/shadow, scene-wide versus local cloud, temporal mismatch, OSM incompleteness, wrong buffer, pixel classification, VLM hallucination and stale cached results.

## 10. Frontend/UX Audit

**Already good:** the interaction is immediately understandable; map is the primary canvas; client-only Leaflet avoids SSR trouble; returned image/date/cloud metadata and caveats are meaningful trust gestures; loading text does not falsely claim actual backend stage.

**Amateur/confusing:** the UI is a standard split-pane developer tool—system font, default Leaflet marker, dense bordered cards, generic blue button, raw coordinates, and an empty panel instruction. It still says AskTheMap. The analysis panel gives model-generated observations the visual status of evidence. The user cannot search a place, see the selected area/buffer, understand Sentinel scale/date before asking, compare imagery, or distinguish “image I inspected” from “facts we calculated.”

**Central experience:** choose a place → see its evidence footprint → ask from a deliberately supported set of questions → inspect a concise answer with a source/date/limitations drawer. The map should remain dominant; chat is a focused query composer, not a generic conversation transcript.

## 11. Recommended Frontend Direction

Keep Next.js, TypeScript, Leaflet and plain CSS for V1. Do not add a design system or state library yet.

- Rename visibly to **Askio** and use a strong single-column mobile sheet over the map.
- Add place/coordinate search before adding chat history. A free geocoder has usage policy/rate-limit implications; start with coordinates and a few preset examples if needed.
- On selection, show a labelled analysis radius, imagery recency/availability and three supported question suggestions.
- Make results a hierarchy: direct conclusion; measured evidence; imagery/source/date; interpretation; limitations. Use a map overlay/footprint rather than a detached thumbnail alone.
- Build polished loading/error/empty states after the reliable data contract exists. Avoid decorative motion until it reinforces state.

The runtime build could not be conclusively verified in this sandbox: it first failed with Windows `spawn EPERM`, then did not produce output when retried outside the sandbox. `npm run lint` prints that `next lint` is deprecated and did not terminate during the audit. The API test suite passed (25 tests); this is a deployment-readiness finding, not evidence that the web source fails compilation.

## 12. Free Deployment Options

| Service | Tier | Current useful limit / constraint | Suitability |
| --- | --- | --- | --- |
| GitHub Pages | Tier 1 | Static only. | Fine for a static frontend, no API. |
| Cloudflare Pages | Tier 1 | 500 builds/month, 20k files; Pages Functions use Workers quota. | Strong static host. [Limits](https://developers.cloudflare.com/pages/platform/limits/) |
| Cloudflare Workers | Tier 2 | 100k req/day but only 10 ms CPU/request free. | Good proxy/rate-limit/cache, **not** rasterio/Python image processing. [Limits](https://developers.cloudflare.com/workers/platform/limits/) |
| Vercel Hobby | Tier 2 | Personal/non-commercial; free quotas and up to 60 s function duration. | Easiest Next deployment; unsuitable as dependable heavy raster backend. [Hobby plan](https://vercel.com/docs/plans/hobby) |
| Netlify free | Tier 2 | Policy/limits change; serverless compute is constrained. | Fine alternative static host; not needed. |
| Render free | Tier 2 / volatile | Cold starts and free-policy availability change. | Do not make core demo depend on it. |
| Hugging Face Spaces | Tier 2 | Free CPU capacity can sleep/queue and availability changes. | Demo fallback, not service foundation. |
| Supabase/Neon/D1 | Tier 2 | Free allocations/policies; database currently unnecessary. | Do not add for V1. |

No cloud option above makes the present Python + GDAL + remote COG + VLM pipeline a reliably available true-$0 public backend. A static frontend is truly free; a full live application is $0 only within someone else's changing quotas.

## 13. Recommended $0 Deployment Stack

**V1 public portfolio:** GitHub repository + GitHub Actions CI + Cloudflare Pages (or Vercel Hobby) for the static Next frontend, with a clear “live analysis runs locally / demo mode” experience. Use pre-generated sample evidence responses for the public site; do not embed a VLM key.

**V1 live development/demo:** FastAPI and optional local Ollama on the laptop; Planetary Computer accessed anonymously; a small disk cache outside the repository. Use Cloudflare Tunnel only for temporary supervised demonstrations if necessary. This is honest about operational reality and preserves the serious GIS pipeline.

When a reliable free Python host becomes available to the project, deploy the existing monolith as one API service with environment secrets and production CORS. Do not split it into services.

## 14. Cost Analysis

| Component | Current | Recommended | Cost at V1 | Main limitation |
| --- | --- | --- | ---: | --- |
| Frontend | Local Next dev server | Cloudflare Pages static site | $0 | Static only; free limits can change. |
| API | Local FastAPI | Local FastAPI for live analysis | $0/month | Laptop availability. |
| Satellite data | Planetary Computer Sentinel-2 | Same, provider-adaptable | $0 | Throttling/service dependency. |
| Model | Retired Gemini default / OpenRouter free | Optional local VLM; hosted free only for experiments | $0 | Laptop hardware or hosted quotas. |
| Database | None | None / local cache | $0 | No history/shared state. |
| Mapping | OSM public tiles | Same for low-volume demo | $0 | Must respect tile usage policy; no high-volume assumption. |

## 15. Code Quality

**Strong:** compact boundaries; Pydantic input/output types; sensible stage-specific error mapping; duplicated prompt avoided; VLM schema is provider-neutral; raster boundary regression is documented; CI exists.

**Critical/high:** retired default model; secret-bearing asset HREF exposure; no abuse controls; no evidence contract. **Medium:** silent invalid provider fallback; `sys.path` packaging shortcut; no dependency lock for Python; API/frontend schemas manually duplicated; broad CORS method/header allowance; metadata uses a possibly temporary signed HREF; code/product naming mismatch; next-lint deprecation. **Low:** no structured logging/request IDs, no accessibility pass, no local developer bootstrap for cross-platform shell (`scripts/dev.sh` only).

## 16. Testing

There are 25 passing tests: request bounds, response models, query happy/error paths, OpenRouter JSON parsing, and image edge clamping. That is meaningful early coverage.

Smallest high-value additions:

1. STAC search contract tests: no results, missing visual asset, malformed metadata, date/cloud selection.
2. Evidence calculations: CRS/buffer correctness, known tiny raster/known vector fixtures, empty/cloudy input.
3. Provider factory/config: rejected invalid provider, retired/unsupported model health/readiness state.
4. Endpoint: no signed HREF in payload; rate-limit/cache behavior; provider 401/429/503 mapping.
5. Frontend: one contract test for success/error/evidence rendering and a mobile smoke test.

Do not start with browser E2E against live satellite/VLM APIs; their variability makes them poor CI fixtures.

## 17. Performance

The primary bottleneck is remote COG access (the project measured ~37 seconds), followed by VLM inference. The PNG is serialized twice (provider and response) and base64 expands it by roughly one-third. The frontend also loads map tiles from a public third-party service.

Cache by normalized point/buffer, scene ID, imagery processing parameters and question/evidence version; use short TTLs and a bounded disk cache. Cache STAC selections/rendered image separately from language interpretation. Prefer a remote rendered preview/tile endpoint only after measuring its visual/data trade-off. Never cache an answer without recording its acquisition date and evidence version.

## 18. Vendor Lock-In

Gemini/OpenRouter are already isolated behind `BaseVLM`; retain that small interface but introduce a separate `EvidenceProvider` only when the second real data source exists. Planetary Computer is moderately replaceable because STAC, COG and PySTAC are open standards; signing/render peculiarities belong in one adapter. Leaflet is low lock-in. OSM public tiles are replaceable but usage-limited. Next.js is moderately coupled but no migration is justified. No database/platform lock-in exists today.

## 19. What I Would Delete

- The retired Gemini model default immediately (not Gemini capability itself).
- The `asset_href` response field and every UI/type reference to it.
- The claim that VLM “supporting evidence” is evidence; rename it `visual_observations` until a truth layer exists.
- Any assumption that a single newest RGB scene can answer arbitrary questions about any Earth location.
- A future database, auth system, chat history, job queue, microservice split, Kubernetes and managed GIS stack from V1 plans.
- The `next lint` script after replacing it with direct ESLint configuration; do not keep a deprecated CI command.

## 20. What I Would Build Next

| Rank | Improvement | Impact | Difficulty | Cost | Technical / portfolio value |
| ---: | --- | --- | --- | --- | --- |
| 1 | Restore a working no-key/evidence-only flow; remove retired default and signed URL. | High | Low | $0 | High |
| 2 | Add `EvidenceRecord` and one deterministic capability: NDVI + scene/date/cloud quality in a declared buffer. | Very high | Medium | $0 | Very high |
| 3 | Add rate limit, bounded cache and readiness diagnostics. | High | Low–medium | $0 | High |
| 4 | Add OSM road/building proximity/count evidence for one urban question. | High | Medium | $0 | Very high |
| 5 | Redesign the selection-to-evidence UI and finish Askio rename. | High | Medium | $0 | High |

## 21. Portfolio/Research Value

Today an experienced reviewer would see solid API hygiene and a thoughtful prototype, but also “another VLM wrapper over satellite imagery.” The project becomes compelling when it makes a narrow, verifiable claim: the repository can reproduce an answer from named scenes, calculations, buffers, quality checks and source metadata, then use a model only to communicate it. Publish a few fixed case studies with expected metrics, diagrams and tests—not only screenshots. That demonstrates geospatial engineering, remote sensing literacy, uncertainty handling and product judgment.

## 22. Final Architecture Diagram

```text
                       ┌─────────────────────────┐
                       │ Askio Next.js + Leaflet  │
                       │ select place / buffer    │
                       └───────────┬─────────────┘
                                   HTTPS
                       ┌───────────▼─────────────┐
                       │ FastAPI monolith         │
                       │ validation + rate limit  │
                       │ small disk cache         │
                       └───────┬─────────┬───────┘
                               │         │
              ┌────────────────▼─┐   ┌──▼─────────────────┐
              │ Evidence engine  │   │ Optional explainer  │
              │ STAC/COG + OSM   │──►│ local VLM or hosted │
              │ metrics + quality│   │ receives facts only │
              └───────┬──────────┘   └──┬─────────────────┘
                      │                 │
              ┌───────▼─────────────────▼───────┐
              │ Typed response                    │
              │ EvidenceRecord + Interpretation   │
              │ sources, dates, method, limits    │
              └───────────────────────────────────┘
```

## 23. Recommended Implementation Roadmap

### Phase 0 — Fix dangerous problems

**DO NOW:** remove signed HREF from all client payloads; rotate any potentially exposed secret; stop defaulting to a retired Gemini model; validate provider configuration; add a readiness endpoint that does not leak secrets; add basic rate/concurrency controls before any public API URL.

### Phase 1 — Stabilize V1

**DO NOW:** support evidence-only responses when no VLM is configured; test the chosen provider/model on the actual account; make crop date, quality and actual bounds explicit; repair CI lint command and obtain a reproducible production build locally/CI.

### Phase 2 — Simplify architecture

**DO NOW:** retain one FastAPI service and the existing frontend; remove the client asset HREF and prose-as-evidence naming. **DO NOT DO:** microservices, auth, database, queues, Kubernetes.

### Phase 3 — Improve geospatial grounding

**DO NOW:** define 3–5 supportable questions and implement one evidence pipeline at a time, beginning with NDVI/quality/metadata. **DO LATER:** two-date change analysis and OSM vector metrics. **OPTIONAL:** local VLM explanation.

### Phase 4 — Improve frontend

**DO LATER:** rename to Askio, design evidence-first result hierarchy, add footprint/buffer overlay, onboarding/presets, responsive bottom sheet, accessibility and graceful retry states. **DO NOT DO:** generic chat-dashboard styling or decoration-first animation.

### Phase 5 — Deploy for $0

**DO NOW:** deploy static portfolio/demo frontend on Cloudflare Pages or Vercel Hobby with no secrets. **DO LATER:** deploy monolithic API only when a suitable free runtime is verified at that date. **DO NOT DO:** pretend a quota-limited hosted VLM + Python/GDAL backend is a reliable permanent $0 service.

### Phase 6 — Optional advanced features

**OPTIONAL:** local Ollama VLM, time-series comparisons, region highlighting, reproducible case-study notebooks. Add each only after its evidence contract and test fixture exist.

### Direct answer

If this were my personal project, at $0, I would choose **Next.js/Leaflet static frontend + one local FastAPI evidence monolith + Planetary Computer STAC/COGs + small disk cache + deterministic Sentinel/OSM measurements + optional local Qwen-family VLM through Ollama/llama.cpp**. I would host the frontend freely and run live analysis locally for development and demos. This maximizes reproducibility, privacy, learning value and technical credibility while avoiding paid inference and a fragile serverless raster stack. I would only add hosted Gemini/OpenRouter as a clearly labelled, rate-limited enhancement—not as the thing that makes geographic claims true.
