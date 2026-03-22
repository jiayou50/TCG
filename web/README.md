# Web Frontend

React + TypeScript app bootstrapped with Vite.

## Setup

```bash
cd web
npm install
```

## Development

Start the frontend dev server:

```bash
cd web
npm run dev
```

This frontend fetches `GET /api/game-state` on load.
The Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8000/*`.

Run the backend API server first:

```bash
cd ../backend
uvicorn tcg_engine.api:app --app-dir src --reload
```

## Production build

```bash
npm run build
npm run preview
```

## Backend server

The backend now uses FastAPI for a lightweight JSON API.
