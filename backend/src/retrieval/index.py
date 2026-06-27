"""Track B (Daril) — Build the persistent multilingual vector index.

Embeds title + excerpt + content with EMBED_MODEL into a persistent ChromaDB at
data/sources/index/. Body owned by Daril (PROTOCOL.md Track B-B2).
"""
from __future__ import annotations


def build_index() -> None:
    """Embed data/sources/pages.json into ChromaDB with full metadata."""
    raise NotImplementedError("Track B-B2: Daril")


def get_collection():
    """Return the persistent Chroma collection used by search()."""
    raise NotImplementedError("Track B-B2: Daril")
