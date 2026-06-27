"""Track B (Daril) — Ingest Integreat pages into data/sources/pages.json.

Signature seam (PROTOCOL.md §4.3 / Track B-B1). Body owned by Daril.
"""
from __future__ import annotations


def fetch_pages(languages: list[str] | None = None) -> list[dict]:
    """Fetch + normalize all pages for the configured region across `languages`.

    Each page normalizes to:
        {id, title, url, content, excerpt, last_updated, language,
         parent_id, available_languages}
    """
    raise NotImplementedError("Track B-B1: Daril")


def run() -> None:
    """Fetch and write data/sources/pages.json."""
    raise NotImplementedError("Track B-B1: Daril")
