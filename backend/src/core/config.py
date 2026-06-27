"""Central configuration. Reads env (and an optional repo-root .env).

All model/provider settings are env-driven so the LLM and embedding model can be
swapped (cloud -> self-hosted open weights) without code changes — see
constitution principle on swappable, self-hostable models.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load a repo-root .env if present (does not override real environment vars).
# APP_ROOT env var allows override in containers where the file-relative path doesn't match.
_REPO_ROOT = Path(os.getenv("APP_ROOT", "")) if os.getenv("APP_ROOT") else Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # --- LLM (OpenAI-compatible endpoint; works for OpenAI, vLLM, Ollama, etc.) ---
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # --- Embeddings (multilingual so a non-German query matches German pages) ---
    embed_model: str = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")

    # --- Integreat source region (no city hardcoded in code) ---
    integreat_region: str = os.getenv("INTEGREAT_REGION", "testumgebung-frag-integreat")

    # --- Conversation history (full history passed to the LLM, token-capped) ---
    # ~4000 tokens ≈ 38 turns ≈ 19 back-and-forths — well beyond a real session,
    # at ~$0.04/turn extra on GPT-4o, negligible on mini models. Oldest turns are
    # dropped first on the client when this budget is exceeded.
    max_history_tokens: int = int(os.getenv("MAX_HISTORY_TOKENS", "4000"))

    # --- Trusted web-fetch whitelist (constitution VI: no open-web crawl) ---
    # Only these domains may be fetched to supplement RAG. Extend deliberately.
    trusted_domains: tuple[str, ...] = (
        "integreat-app.de",
        "integreat.app",
        "bamf.de",
        "gesetze-im-internet.de",
        "stwm.de",  # Studentenwerk München
        "muenchen.de",
        "auswaertiges-amt.de",
        "make-it-in-germany.com",
        "arbeitsagentur.de",
        "anerkennung-in-deutschland.de",
    )

    # --- Paths ---
    repo_root: Path = _REPO_ROOT
    journeys_dir: Path = _REPO_ROOT / "data" / "journeys"
    sources_dir: Path = _REPO_ROOT / "data" / "sources"
    index_dir: Path = _REPO_ROOT / "data" / "sources" / "index"


settings = Settings()
