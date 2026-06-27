# Backend: FastAPI + Uvicorn
# Build context must be the REPO ROOT (not backend/), so paths below are relative to repo root.
# Build with: docker build -f backend/Dockerfile -t compass-backend .
FROM python:3.12-slim

WORKDIR /app

# System deps (needed for some native extensions in chromadb/sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (copy pyproject first for layer caching)
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# Copy app source
COPY backend/src/ ./src/

# Copy data (journey graphs, sources index) — loaded at startup
COPY data/ ./data/

# Config: the app resolves paths from APP_ROOT. Inside the container, /app is the root.
ENV PYTHONPATH=/app/src
ENV APP_ROOT=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
