"""Track A (Harsh) — Slot filler (A5). Stub for Phase 0; filled in A5."""
from __future__ import annotations

from core.types import Option


def chips_for(stage: dict, slot: str) -> tuple[str, list[Option]]:
    """Return (prompt, chips) from the stage's option_sets for a missing slot.
    Chips come from the journey template, never LLM-generated."""
    raise NotImplementedError("Track A-A5")
