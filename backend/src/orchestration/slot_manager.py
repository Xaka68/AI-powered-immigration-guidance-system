"""Track A (Harsh) — Slot manager (A3).

Merges newly selected/extracted slots into the session. Returns a new Session
(does not mutate the input) so turns stay easy to reason about.
"""
from __future__ import annotations

from core.types import Session


def merge_slots(session: Session, new_slots: dict) -> Session:
    """Return a copy of `session` with `new_slots` merged in.

    None values are ignored so a missing extraction never clears a known slot.
    """
    merged = dict(session.slots)
    for key, value in new_slots.items():
        if value is not None:
            merged[key] = value
    return session.model_copy(update={"slots": merged})
