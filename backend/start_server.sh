#!/usr/bin/env bash
set -euo pipefail

# Use local Python environment.
source ./myenv/bin/activate

# Start the backend FastAPI development server.
uvicorn tcg_engine.api:app --app-dir src --reload
