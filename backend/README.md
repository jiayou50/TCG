# Backend (Python) - Core Game Logic

This package contains the core rules engine and game state for a Magic-like TCG.

## Goals

- Keep rules deterministic and testable.
- Keep core logic UI-agnostic.
- Expose simple interfaces for a future API server and AI agents.

## Quick start

```bash
cd backend
python -m unittest discover -s tests -p 'test_*.py'
```

## Scope of this initial scaffold

- Basic game state model
- Turn phases
- Zone movement
- A minimal legal-actions API
- Card schema with mana cost and card type
- Creature and land support (including the five basic lands)
- Mana pool utilities and mana cost payment checks

This is a foundation for implementing full Magic: The Gathering rules incrementally.
