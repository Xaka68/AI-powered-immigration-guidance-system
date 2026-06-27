"""Track B (Daril) — Semantic search over the multilingual index.

Signature is fixed (PROTOCOL.md §4.3); body owned by Daril (Track B-B3).
Track A imports this exact signature.
"""
from __future__ import annotations

from core.types import Source


def search(query: str, city: str | None, language: str, k: int = 5) -> list[Source]:
    """Return top-k citable Sources, preferring pages available in `language`
    and boosting by `city` when set."""
    raise NotImplementedError("Track B-B3: Daril")
