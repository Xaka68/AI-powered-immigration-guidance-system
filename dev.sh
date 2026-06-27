#!/usr/bin/env bash
# Run the whole app locally: FastAPI backend (:8000) + Vite frontend.
# Usage:  ./dev.sh        (Ctrl+C stops both)
#
# Requires: backend/.venv (python deps incl. langgraph + retrieval) and
# frontend/node_modules (npm install). The backend needs LLM_API_KEY in .env
# for grounded answers, and a built index at data/sources/index.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "→ backend  : http://localhost:8000   (FastAPI)"
echo "→ frontend : http://localhost:8080   (Vite — open this in your browser)"
echo

( cd "$ROOT/backend" && .venv/bin/python -m uvicorn api.main:app --app-dir src --port 8000 ) &
BACK=$!
( cd "$ROOT/frontend" && npm run dev ) &
FRONT=$!

trap 'echo; echo "stopping…"; kill "$BACK" "$FRONT" 2>/dev/null || true' EXIT INT TERM
wait
