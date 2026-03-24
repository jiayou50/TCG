#!/usr/bin/env bash
set -euo pipefail

# Start the backend FastAPI development server.
uvicorn tcg_engine.api:app --app-dir src --reload
