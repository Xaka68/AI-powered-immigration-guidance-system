#!/bin/bash
# Entrypoint: build the index on first start if it doesn't exist, then run the server.
set -e

INDEX_DIR="/app/data/sources/index"

if [ ! -d "$INDEX_DIR" ] || [ -z "$(ls -A $INDEX_DIR 2>/dev/null)" ]; then
    echo "=== Index not found. Building retrieval index (first-time only)... ==="
    python -m retrieval.ingest || echo "WARNING: ingest failed, continuing without index"
    python -m retrieval.index || echo "WARNING: index build failed, continuing without index"
    echo "=== Index build complete ==="
fi

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
