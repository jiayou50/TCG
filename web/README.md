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

By default, Vite is configured to bind to `0.0.0.0`, so the app can be opened from other machines on the same local network.

### Access from another device on the same Wi-Fi/LAN

1. Start the frontend (`npm run dev`).
2. Find your computer's local IP address (example: `192.168.1.25`).
3. Open `http://<local-ip>:5173` from the other device.

Example URL:

```text
http://192.168.1.25:5173
```

If needed, allow inbound connections on port `5173` in your firewall.

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
