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

    # --- Speech-to-text (voice input). OpenAI-compatible audio transcription. ---
    stt_model: str = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")

    # --- Integreat source region (no city hardcoded in code) ---
    integreat_region: str = os.getenv("INTEGREAT_REGION", "testumgebung-frag-integreat")

    # --- Paths ---
    repo_root: Path = _REPO_ROOT
    journeys_dir: Path = _REPO_ROOT / "data" / "journeys"
    sources_dir: Path = _REPO_ROOT / "data" / "sources"
    index_dir: Path = _REPO_ROOT / "data" / "sources" / "index"

    @property
    def llm_external(self) -> bool:
        """True if the LLM endpoint is a remote/third-party host (personal data
        leaves the device's trust boundary). False for a self-hosted local endpoint
        (localhost / 127.0.0.1) — the privacy-preserving deployment."""
        from urllib.parse import urlparse

        host = (urlparse(self.llm_base_url).hostname or "").lower()
        return host not in ("localhost", "127.0.0.1", "::1", "")


settings = Settings()
