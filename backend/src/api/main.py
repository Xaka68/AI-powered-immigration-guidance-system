"""FastAPI app.

A6: `/chat` runs the real pipeline (router -> graph -> slots -> retrieval ->
handoff). The journey registry is loaded once at startup by directory-scanning
data/journeys/ — dropping in a new journey JSON + restart makes it available with
no code change.

Run from repo root:
    uvicorn api.main:app --app-dir backend/src --port 8000 --reload
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from core.types import ChatRequest, ChatResponse
from orchestration.loader import load_journeys
from orchestration.pipeline import run_turn, run_turn_stream

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


@app.post("/chat/stream")
def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Server-Sent Events: live reasoning steps as the agent works, then the final
    answer. Each line is `event: step|done` + `data: <json>`. Falls back cleanly —
    the client can still use POST /chat if it doesn't consume the stream."""

    def gen():
        try:
            for ev in run_turn_stream(req, _REGISTRY):
                if ev.get("type") == "response":
                    payload = ev["data"].model_dump()
                    yield f"event: done\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                else:
                    yield f"event: step\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except Exception as exc:  # noqa: BLE001 — surface a clean error event
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
