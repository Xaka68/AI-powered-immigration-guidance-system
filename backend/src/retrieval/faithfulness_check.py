"""Track B (Daril) — Faithfulness pass.

Drops/flags any next_step or document not supported by the sources, and sets
`uncertainty` when freshness is missing. Signature fixed (PROTOCOL.md §4.3);
body owned by Daril (Track B-B5).
"""
from __future__ import annotations

from core.types import Source, StructuredAnswer


def check(answer: StructuredAnswer, sources: list[Source]) -> StructuredAnswer:
    """Return a faithfulness-filtered copy of `answer`."""
    raise NotImplementedError("Track B-B5: Daril")
