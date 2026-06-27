"""Track A (Harsh) — Graph engine (A2). Stub for Phase 0; filled in A2.

Pure, LLM-free transitions over an authored journey graph.
"""
from __future__ import annotations

from core.types import Session


def missing_slots(stage: dict, slots: dict) -> list[str]:
    """Return required_slots for `stage` that are not yet present in `slots`."""
    raise NotImplementedError("Track A-A2")


def next_stage(journey: dict, stage_id: str, slots: dict) -> str | None:
    """Apply next_stage_rules / escalation_exits. May return a stage id,
    'ROUTE:<journey_id>', 'HANDOFF', or None."""
    raise NotImplementedError("Track A-A2")


def resolve(journey: dict, session: Session) -> dict:
    """Resolve current stage + transitions for the pipeline."""
    raise NotImplementedError("Track A-A2")
