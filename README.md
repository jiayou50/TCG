# TCG Monorepo

This repository now contains two projects:

- `backend/`: Python core game logic engine (Magic-like rules framework)
- `web/`: Web frontend scaffold

## Why this structure

This split keeps game rules deterministic and testable in Python while allowing fast UI iteration in a web app.

## Getting started

### Backend

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
```

### Frontend

Open `web/index.html` in a browser to view the scaffold UI.

## Current backend capabilities

- Domain models for cards, players, zones, phases, and game state
- Basic operations: draw card, move card between zones, phase progression
- Minimal legal-action API (`get_legal_actions` / `apply_action`)
- Unit tests for the core operations

## Next steps

1. Expand Magic timing windows and stack behavior.
2. Add mana system and spell casting costs.
3. Add FastAPI service in `backend/` for multiplayer and AI adapters.
4. Replace `web/` scaffold with React + TypeScript app connected to the API.
