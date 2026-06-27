"""FastAPI app.

A6: `/chat` runs the real pipeline (router -> graph -> slots -> retrieval ->
handoff). The journey registry is loaded once at startup by directory-scanning
data/journeys/ — dropping in a new journey JSON + restart makes it available with
no code change.

Run from repo root:
    uvicorn api.main:app --app-dir backend/src --port 8000 --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.types import ChatRequest, ChatResponse
from orchestration.loader import load_journeys
from orchestration.pipeline import run_turn

# Loaded at startup; the dynamic dir-scan is the generalizability mechanism.
_REGISTRY: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _REGISTRY
    _REGISTRY = load_journeys()
    yield


app = FastAPI(title="Integreat Compass API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "journeys": sorted(_REGISTRY)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return run_turn(req, _REGISTRY)
