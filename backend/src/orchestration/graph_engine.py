"""Track A (Harsh) — Graph engine (A2).

Pure, deterministic, LLM-free navigation of an authored journey graph. This is
where accuracy lives: transitions come only from the authored JSON, never from a
model. Every function is a pure function of (journey, stage, slots).
"""
from __future__ import annotations

CONTENT_STAGE_TYPES = {
    "action_plan",
    "documents",
    "appointment_contact",
    "translation_communication",
    "follow_up",
}


def first_stage_id(journey: dict) -> str:
    return journey["stages"][0]["id"]


def get_stage(journey: dict, stage_id: str) -> dict:
    for stage in journey["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise KeyError(f"Stage '{stage_id}' not in journey '{journey['id']}'")


def missing_slots(stage: dict, slots: dict) -> list[str]:
    """Required slots for `stage` that are absent or None in `slots`."""
    return [s for s in stage.get("required_slots", []) if slots.get(s) is None]


def is_content_stage(stage: dict) -> bool:
    """A content stage renders a grounded answer and needs a retrieval_query."""
    return stage["type"] in CONTENT_STAGE_TYPES and bool(stage.get("retrieval_query"))


def check_escalation(stage: dict, slots: dict) -> str | None:
    """Evaluate `escalation_exits`. Returns a `go_to` target or None.

    Supported condition grammar: ``slot:<name> == <value>``.
    """
    for exit_rule in stage.get("escalation_exits", []):
        if _eval_condition(exit_rule["condition"], slots):
            return exit_rule["go_to"]
    return None


def next_stage(journey: dict, stage_id: str, slots: dict) -> str | None:
    """Apply `next_stage_rules` for the current stage once its slots are filled.

    Returns a target: a stage id in this journey, ``ROUTE:<journey_id>``,
    ``HANDOFF``, or None when no rule matches.
    """
    stage = get_stage(journey, stage_id)
    for rule in stage.get("next_stage_rules", []):
        if slots.get(rule["if_slot"]) == rule["equals"]:
            return rule["go_to"]
    return None


def _eval_condition(condition: str, slots: dict) -> bool:
    # Only ``slot:<name> == <value>`` is supported today; extend deliberately.
    cond = condition.strip()
    if cond.startswith("slot:") and "==" in cond:
        left, right = cond.split("==", 1)
        name = left.replace("slot:", "").strip()
        want = right.strip().strip("'\"")
        return str(slots.get(name)) == want
    return False
