"""Track B (Daril) — Embedding provider abstraction (swappable cloud <-> OSS).

Model chosen by ``settings.embed_model``:
- ``text-embedding-3-*`` -> OpenAI API (fast; uses the same LLM_* credentials).
- name containing ``e5`` -> local sentence-transformers with query/passage prefixes.
- any other name -> local sentence-transformers, no prefix.

This is the constitution's "swap cloud -> self-hosted open model" seam: flip
EMBED_MODEL to ``intfloat/multilingual-e5-large`` to go fully OSS, no code change.
"""
from __future__ import annotations

import os
import time
from functools import lru_cache

from core.config import settings

_MODEL = settings.embed_model
_IS_OPENAI = _MODEL.startswith("text-embedding")
_IS_E5 = "e5" in _MODEL.lower()

# OpenAI caps a request at 300k tokens; non-Latin scripts (ar/fa/uk) are
# token-heavy, so we batch by an estimated token budget, not a fixed item count.
_OPENAI_TOKEN_BUDGET = 120_000
_OPENAI_MAX_ITEMS = 256


def _prefixed(text: str, kind: str) -> str:
    return f"{kind}: {text}" if _IS_E5 else text  # e5 trained with these prefixes


@lru_cache(maxsize=1)
def _st_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL)


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    api_key = settings.llm_api_key or os.getenv("OPENAI_API_KEY") or None
    if not api_key:
        raise RuntimeError(
            "EMBED_MODEL is an OpenAI model but no LLM_API_KEY/OPENAI_API_KEY is set."
        )
    return OpenAI(base_url=settings.llm_base_url or None, api_key=api_key, max_retries=6)


def _openai_batches(texts: list[str]):
    batch: list[str] = []
    est = 0
    for t in texts:
        t_est = len(t) + 8  # chars as a conservative token proxy
        if batch and (est + t_est > _OPENAI_TOKEN_BUDGET or len(batch) >= _OPENAI_MAX_ITEMS):
            yield batch
            batch, est = [], 0
        batch.append(t)
        est += t_est
    if batch:
        yield batch


def _embed_with_retry(client, batch: list[str], attempts: int = 6):
    from openai import RateLimitError

    for i in range(attempts):
        try:
            return client.embeddings.create(model=_MODEL, input=batch)
        except RateLimitError:
            if i == attempts - 1:
                raise
            time.sleep(min(2**i, 30))  # exponential backoff, capped at 30s


def _embed(texts: list[str], kind: str) -> list[list[float]]:
    if not texts:
        return []
    if _IS_OPENAI:
        client = _openai_client()
        out: list[list[float]] = []
        for batch in _openai_batches(texts):
            resp = _embed_with_retry(client, batch)
            out.extend(d.embedding for d in resp.data)
        return out
    vecs = _st_model().encode(
        [_prefixed(t, kind) for t in texts], normalize_embeddings=True
    )
    return vecs.tolist()


def embed_queries(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "query")


def embed_passages(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "passage")
