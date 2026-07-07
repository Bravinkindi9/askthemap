# AskTheMap Web

Next.js frontend with an interactive Leaflet map. Users click a location, type a
question, and see a structured analysis (summary, confidence, supporting
evidence, caveats) alongside the exact satellite tile the AI analyzed, so the
answer can be visually verified rather than taken on faith.

## Setup

```bash
cd apps/web
npm install
```

## Configuration

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Default API URL is `http://localhost:8000`. Change `NEXT_PUBLIC_API_URL` if your API runs elsewhere.

## Run

```bash
npm run dev
```

Open http://localhost:3000

## Build

```bash
npm run build
npm start
```
