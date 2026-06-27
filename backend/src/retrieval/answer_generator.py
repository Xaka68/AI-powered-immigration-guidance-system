"""Track B (Daril) — Grounded answer generation.

Signature is fixed (PROTOCOL.md §4.3); body owned by Daril (Track B-B4).
The system prompt MUST forbid any claim not in `sources` and forbid inventing
steps/deadlines/documents.
"""
from __future__ import annotations

from core.types import Source, StructuredAnswer


def generate_answer(
    stage_goal: str,
    user_language: str,
    sources: list[Source],
    slots: dict,
) -> StructuredAnswer:
    """Produce a StructuredAnswer in `user_language`, grounded only in `sources`."""
    raise NotImplementedError("Track B-B4: Daril")
