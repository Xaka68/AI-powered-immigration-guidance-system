"""Track A (Harsh) — Handoff generator (A7).

Builds a minimal, counselor-facing summary from the session — NOT the raw chat
transcript. The user reviews/edits it and consent is gated client-side (D7)
before anything is shared.
"""
from __future__ import annotations

from core.types import HandoffSummary, Session, Source

# Slots that are safe, useful context for a counselor. Anything else is omitted
# (privacy by minimization).
_CONTEXT_LABELS = {
    "city": "City",
    "housing_status": "Housing",
    "language": "Preferred language",
    "child_age": "Child age",
    "employment_status": "Employment",
}


def build_summary(
    session: Session,
    sources: list[Source],
    journey: dict | None = None,
) -> HandoffSummary:
    goal = "Needs help with their current step."
    if journey is not None:
        goal = f"Needs help with: {journey['title']}."
    elif session.journey_id:
        goal = f"Needs help with: {session.journey_id}."

    known_context = [
        f"{label}: {session.slots[slot]}"
        for slot, label in _CONTEXT_LABELS.items()
        if session.slots.get(slot) is not None
    ]

    open_questions: list[str] = []
    if not sources:
        open_questions.append("No trusted source covered this case — please verify.")
    if session.slots.get("housing_status") in (None, "temporary"):
        open_questions.append("Confirm the user's current accommodation situation.")

    urgency = str(session.slots.get("urgency") or "normal")

    return HandoffSummary(
        user_goal=goal,
        known_context=known_context,
        sources_consulted=[s.title for s in sources],
        open_questions=open_questions,
        urgency=urgency,
    )
