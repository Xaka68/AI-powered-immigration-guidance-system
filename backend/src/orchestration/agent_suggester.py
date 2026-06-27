"""Agent suggestion — T018 (US4 Phase 4).

After a grounded answer, decide whether a specialist agent would concretely help
the user next. Returns AgentSuggestion or None. Conservative by design — only
fires when the fit is obvious. Constitution VII: suggestion only; the user must
consent before the agent activates.
"""
from __future__ import annotations

import json
import logging

from core.types import AgentSuggestion, ConversationTurn, StructuredAnswer

log = logging.getLogger(__name__)

_AGENTS: dict[str, dict] = {
    "housing_finder": {
        "label": "Find real listings",
        "description": "I can search for available apartments and help you draft messages to landlords.",
        "data_needed": ["city"],
    },
    "appointment_booker": {
        "label": "Book a Bürgerbüro appointment",
        "description": "I can check availability and book a slot at your local Citizens' Office.",
        "data_needed": ["city"],
    },
    "document_checker": {
        "label": "Check your documents",
        "description": "I can compare the documents you have against what's required and flag any gaps.",
        "data_needed": [],
    },
}

_SYSTEM = """\
You decide whether to proactively offer a specialist agent after an immigration guidance answer.

Available agents:
- housing_finder: finds real apartment listings and drafts landlord messages.
  Offer ONLY after a conversation clearly about finding or renting a flat.
- appointment_booker: books Citizens' Office (Bürgerbüro) appointment slots.
  Offer ONLY after Anmeldung / address-registration advice where booking an
  appointment is the obvious, concrete next step.
- document_checker: compares documents the user has vs. what they need.
  Offer ONLY after a substantive discussion about required documents where the
  user seems uncertain about what they have.

Rules:
- Output {"suggest": false} in most cases. Be conservative.
- Only suggest when the fit is obvious and the agent provides a concrete next action.
- Never suggest for general questions, greetings, or unrelated topics.
- Output raw JSON only. Exactly one of:
  {"suggest": false}
  {"suggest": true, "agent_id": "<one of the three ids above>"}
"""

_SCHEMA = {
    "type": "object",
    "properties": {
        "suggest": {"type": "boolean"},
        "agent_id": {
            "type": "string",
            "enum": ["housing_finder", "appointment_booker", "document_checker"],
        },
    },
    "required": ["suggest"],
}


def suggest(
    history: list[ConversationTurn],
    answer: StructuredAnswer,
    slots: dict,
) -> AgentSuggestion | None:
    """Return an AgentSuggestion if a specialist agent clearly fits, else None."""
    from core.llm import complete

    recent = history[-6:]
    conv = "\n".join(f"{t.role.upper()}: {t.content}" for t in recent)
    user_msg = (
        f"RECENT ANSWER: {answer.short_answer}\n\n"
        f"CONVERSATION:\n{conv}\n\n"
        "Should a specialist agent be offered? Return JSON."
    )

    try:
        result = complete(_SYSTEM, user_msg, json_schema=_SCHEMA)
        if isinstance(result, str):
            result = json.loads(result)
        if not result.get("suggest"):
            return None
        agent_id = result.get("agent_id")
        if agent_id not in _AGENTS:
            return None
        meta = _AGENTS[agent_id]
        return AgentSuggestion(
            agent_id=agent_id,
            label=meta["label"],
            description=meta["description"],
            data_needed=meta["data_needed"],
        )
    except Exception as exc:
        log.warning("agent_suggester error (non-fatal): %s", exc)
        return None
