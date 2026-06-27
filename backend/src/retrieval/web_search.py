"""Web-search tool — the agent's fallback when the indexed Integreat corpus does
not contain enough to answer.

Default backend: DuckDuckGo via `ddgs` (no API key, works out of the box).
Returns `Source` objects, so the agent and its citations work unchanged. To use a
different provider (Tavily, Serper, or your own tool), just reimplement
`search()` to return `list[Source]` — nothing else changes.
"""
from __future__ import annotations

import logging

from core.types import Source

log = logging.getLogger(__name__)


def search(query: str, k: int = 5) -> list[Source]:
    """Return up to `k` web results as Sources. Returns [] on any failure
    (network/rate-limit) so the agent degrades gracefully."""
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=k)
    except Exception as exc:  # noqa: BLE001
        log.warning("web search failed: %s", exc)
        return []

    out: list[Source] = []
    for r in results or []:
        url = r.get("href") or r.get("url") or ""
        if not url:
            continue
        out.append(
            Source(
                title=(r.get("title") or url)[:200],
                url=url,
                last_updated=None,  # the web rarely exposes a reliable date
                language="",
                excerpt=(r.get("body") or "")[:500],
            )
        )
    return out
