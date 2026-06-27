"""Track A (Harsh) — Slot filler (A5).

When the graph reports a missing slot, emit the chips for it straight from the
journey template — options-first, and never LLM-generated, so the branch set
stays bounded and safe.
"""
from __future__ import annotations

import json

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


def resolve_from_text(stage: dict, slot: str, message: str) -> str | None:
    """Try to resolve a free-text user reply to one of the authored option ids.

    Used so a user can type "yes" or "I found a dorm" instead of tapping a chip
    and still advance the graph. Returns the matched option id, or None if the
    message doesn't clearly match any option.
    """
    from core.config import settings

    option_set = option_set_for(stage, slot)
    if not option_set:
        return None

    if settings.llm_api_key:
        try:
            return _resolve_llm(option_set, message)
        except Exception:
            pass
    return _resolve_heuristic(option_set, message)


def _resolve_llm(option_set: dict, message: str) -> str | None:
    from core import llm as llm_mod

    choices = [{"id": o["id"], "label": o["label"]} for o in option_set["options"]]
    system = (
        "You map a free-text user reply to the single best matching option id. "
        "Reply with ONLY the bare option id string (e.g. has_apartment), "
        "or the word null if nothing clearly matches. No explanation."
    )
    user = (
        f"Question: {option_set['prompt']}\n"
        f"Options: {json.dumps(choices, ensure_ascii=False)}\n"
        f"User said: {message}"
    )
    result = llm_mod.complete(system, user)
    if isinstance(result, str):
        result = result.strip().strip("\"'")
    known_ids = {o["id"] for o in option_set["options"]}
    return result if result in known_ids else None


def _resolve_heuristic(option_set: dict, message: str) -> str | None:
    """Cheap keyword fallback when no LLM key is available."""
    text = message.lower().split()
    # Affirmative words → first option (almost always the "yes / I have one" branch).
    if any(w in text for w in ("yes", "yeah", "yep", "ja", "yea", "sure", "already")):
        return option_set["options"][0]["id"]
    best_id, best_score = None, 0
    for opt in option_set["options"]:
        label_words = set(opt["label"].lower().split())
        msg_words = set(text)
        score = len(label_words & msg_words)
        if score > best_score:
            best_score, best_id = score, opt["id"]
    return best_id if best_score > 0 else None
