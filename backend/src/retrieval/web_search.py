"""Pluggable web-search tool — the agent's fallback when the indexed Integreat
corpus does not contain enough to answer the user.

This is a STUB: it returns no results, so the agent will answer with explicit
uncertainty or hand off to a human. Drop in a real implementation later (the
user has an existing web-search tool) — keep this signature and return `Source`
objects so the agent and its citations keep working unchanged.
"""
from __future__ import annotations

import logging

from core.types import Source

log = logging.getLogger(__name__)


def search(query: str, k: int = 5) -> list[Source]:
    """Return up to `k` web results as Sources. Stub: returns []."""
    log.info("web_search stub (not configured) for query: %s", query)
    return []
