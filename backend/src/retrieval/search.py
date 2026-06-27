"""Track B (Daril) — Semantic search over the multilingual index.

Signature is fixed (PROTOCOL.md §4.3); Track A imports this exact signature.
Top-k semantic retrieval, boosting pages available in the user's language and
(when set) pages mentioning the user's city. Returns citable Sources w/ freshness.
"""
from __future__ import annotations

import json

from core.types import Source
from retrieval.embeddings import embed_queries
from retrieval.index import get_collection


def _dedupe_by_page(matches: list[dict]) -> list[dict]:
    """Keep the best-scoring chunk per page_id (preserves order)."""
    seen: set = set()
    out: list[dict] = []
    for m in matches:
        pid = m["meta"].get("page_id")
        if pid in seen:
            continue
        seen.add(pid)
        out.append(m)
    return out


def search(query: str, city: str | None, language: str, k: int = 5) -> list[Source]:
    """Return top-k citable Sources, preferring pages available in `language`
    and boosting by `city` when set."""
    col = get_collection()
    if col.count() == 0:
        return []

    n = min(max(k * 4, 12), col.count())  # over-fetch to re-rank + dedupe
    res = col.query(query_embeddings=embed_queries([query]), n_results=n)
    metas, dists, docs = res["metadatas"][0], res["distances"][0], res["documents"][0]

    matches = []
    for meta, dist, doc in zip(metas, dists, docs):
        score = 1.0 - dist  # cosine distance -> similarity
        avail = set(json.loads(meta.get("available_languages") or "{}").keys())
        if language and (meta.get("language") == language or language in avail):
            score += 0.05  # answerable in the user's language
        if city and city.lower() in (meta.get("title", "") + doc).lower():
            score += 0.03  # light city relevance boost
        matches.append({"meta": meta, "score": score})

    matches.sort(key=lambda m: m["score"], reverse=True)
    matches = _dedupe_by_page(matches)[:k]

    return [
        Source(
            title=m["meta"].get("title", ""),
            url=m["meta"].get("url", ""),
            last_updated=m["meta"].get("last_updated") or None,
            language=m["meta"].get("language", ""),
            excerpt=m["meta"].get("excerpt", ""),
        )
        for m in matches
    ]
