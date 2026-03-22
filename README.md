# TCG Monorepo

This repository contains two projects:

- `backend/`: Python core game logic engine (Magic-like rules framework)
- `web/`: React + TypeScript frontend powered by Vite

## Why this structure

This split keeps game rules deterministic and testable in Python while allowing fast UI iteration in a modern web app.

## Getting started

### Backend

The backend currently provides the game engine library only (no HTTP API server yet).

To validate and run backend code locally:

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
uvicorn tcg_engine.api:app --app-dir src --reload
```

### Frontend

Start the frontend development server:

```bash
cd web
npm install
npm run dev
```

The Vite dev server is configured to listen on all interfaces (`0.0.0.0`), so it is reachable from other devices on the same Wi-Fi/LAN in addition to localhost.

To connect from another device:

1. Find this machine's local IP address (for example `192.168.1.25`).
2. Keep the frontend running with `npm run dev`.
3. Open `http://<your-local-ip>:5173` from another device on the same network.

Example:

```text
http://192.168.86.250:5173
```

If it does not load, allow incoming connections for port `5173` in your OS firewall.

## Current backend capabilities

- Domain models for cards, players, zones, phases, and game state
- Basic operations: draw card, move card between zones, phase progression
- Minimal legal-action API (`get_legal_actions` / `apply_action`)
- FastAPI service with `/health` and `/game-state`
- Default game state bootstrap for end-to-end frontend integration
- Unit tests for the core operations

## Next steps

1. Expand Magic timing windows and stack behavior.
2. Add mana system and spell casting costs.
3. Expand API from static game state to mutable match state.
4. Add multiplayer and AI adapters.
