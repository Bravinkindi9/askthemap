import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import places, query

app = FastAPI(title="AskTheMap API", version="0.1.0")
rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(places.router)


@app.middleware("http")
async def protect_requests(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_body_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request body too large."})

    now = time.monotonic()
    client_host = request.client.host if request.client else "unknown"
    bucket = rate_limit_buckets[client_host]
    while bucket and now - bucket[0] > settings.rate_limit_window_s:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_requests:
        return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
    bucket.append(now)

    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok"}
