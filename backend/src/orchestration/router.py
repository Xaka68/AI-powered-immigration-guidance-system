"""Track A (Harsh) — Router (A4). Stub for Phase 0; filled in A4.

LLM intent classifier gated to the loaded journey set — never invents a journey.
"""
from __future__ import annotations


def classify(message: str, journeys: dict[str, dict]) -> dict:
    """Map free text onto loaded journeys. Returns
    {'journey_ids': [...], 'extracted_slots': {...}}."""
    raise NotImplementedError("Track A-A4")
