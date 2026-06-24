# AskTheMap Roadmap

## V1 — MVP (Current)

- [x] Project scaffold and documentation
- [x] FastAPI backend with health endpoint
- [x] Geo module: STAC search + image retrieval from Planetary Computer
- [x] VLM integration: provider-agnostic layer with Gemini
- [x] Query endpoint: geo + VLM pipeline
- [x] Next.js frontend with Leaflet map
- [x] End-to-end flow: click → question → answer
- [ ] Basic test suite
- [ ] CI/CD pipeline
- [ ] Deployment

## Future Considerations

- Support additional VLM providers (Claude, GPT-4o)
- Image display in the response (show the satellite tile to the user)
- Time-series analysis (compare imagery across dates)
- Streaming responses (SSE for progressive answer display)
- Caching layer for repeated queries on the same location
- Multi-language support
