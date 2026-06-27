"""Track A (Harsh) — Slot filler (A5).

When the graph reports a missing slot, emit the chips for it straight from the
journey template — options-first, and never LLM-generated, so the branch set
stays bounded and safe.
"""
from __future__ import annotations

from core.types import Option


def option_set_for(stage: dict, slot: str) -> dict | None:
    for option_set in stage.get("option_sets", []):
        if option_set["slot"] == slot:
            return option_set
    return None


def chips_for(stage: dict, slot: str) -> tuple[str, list[Option]]:
    """Return (prompt, chips) for a missing slot from the stage's option_sets.

    Falls back to a generic prompt with no chips (free-text only) if the author
    did not provide an option_set for this slot.
    """
    option_set = option_set_for(stage, slot)
    if option_set is None:
        return (f"Could you tell me your {slot.replace('_', ' ')}?", [])
    chips = [Option(id=o["id"], label=o["label"]) for o in option_set["options"]]
    return (option_set["prompt"], chips)
