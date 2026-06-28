# Backend: FastAPI + Uvicorn + ChromaDB retrieval index (baked at build time).
# Build context must be the REPO ROOT (paths below are relative to repo root):
#   docker build -f backend/Dockerfile -t compass-backend .
#
# NOTE: the build runs ingest + index, so it needs network access (Integreat API)
# and downloads the multilingual-e5 model (~2GB). The container ships with
# retrieval ready — no runtime fetch, fast cold start.
FROM python:3.12-slim

WORKDIR /app

# System deps for native extensions in chromadb / sentence-transformers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only FIRST — avoids pulling ~900MB of CUDA libs.
# App Runner has no GPU; CPU inference is sufficient for embedding generation.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python deps. Copy pyproject + src first so the package resolves.
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src/ ./src/
RUN pip install --no-cache-dir .

# Journey graphs (committed) + a place for the generated index.
COPY data/ ./data/

# Paths resolve from APP_ROOT inside the container.
ENV PYTHONPATH=/app/src
ENV APP_ROOT=/app
ENV PORT=8000

# Bake the retrieval index into the image: fetch Integreat -> embed -> ChromaDB.
# Uses the local e5 model (no API key needed). Fails the build if the index
# can't be built, so a successful image always has working retrieval.
RUN python -m retrieval.ingest && python -m retrieval.index

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
