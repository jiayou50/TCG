# Backend (Python) - Core Game Logic

This package contains the core rules engine and game state for a Magic-like TCG.

## Goals

- Keep rules deterministic and testable.
- Keep core logic UI-agnostic.
- Expose simple interfaces for a future API server and AI agents.

## Quick start

This package is currently a Python rules engine and does **not** include an HTTP server yet.

Run tests to verify backend behavior:

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
```

## Run API server (FastAPI)

```bash
cd backend
uvicorn tcg_engine.api:app --app-dir src --reload
```

Available endpoints:

- `GET /health`
- `GET /game-state` (returns a static default starting game state)

## Scope of this initial scaffold

- Basic game state model
- Turn phases
- Zone movement
- A minimal legal-actions API
- Card schema with mana cost and card type
- Creature and land support (including the five basic lands)
- Mana pool utilities and mana cost payment checks

This is a foundation for implementing full Magic: The Gathering rules incrementally.
