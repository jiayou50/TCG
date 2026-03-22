# TCG Monorepo

This repository contains two projects:

- `backend/`: Python core game logic engine (Magic-like rules framework)
- `web/`: React + TypeScript frontend powered by Vite

## Why this structure

This split keeps game rules deterministic and testable in Python while allowing fast UI iteration in a modern web app.

## Getting started

### Backend

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
uvicorn tcg_engine.api:app --app-dir src --reload
```

### Frontend

```bash
cd web
npm install
npm run dev
```

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
