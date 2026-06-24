#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting AskTheMap development servers..."
echo ""

# Start API
cd "$ROOT_DIR/apps/api"
echo "Starting API on http://localhost:8000"
python -m uvicorn app.main:app --reload --port 8000 &
API_PID=$!

# Start Web
cd "$ROOT_DIR/apps/web"
echo "Starting Web on http://localhost:3000"
npm run dev &
WEB_PID=$!

echo ""
echo "Both servers running. Press Ctrl+C to stop."

trap "kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM
wait
