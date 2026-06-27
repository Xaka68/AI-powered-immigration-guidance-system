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
You decide whether to offer a specialist agent after an immigration guidance answer.

Available agents:
- housing_finder: finds real apartment listings and drafts landlord messages.
  Suggest when the CURRENT TOPIC is clearly about finding or renting a flat / apartment.
- appointment_booker: books Citizens' Office (Bürgerbüro) appointment slots.
  Suggest when the CURRENT TOPIC is Anmeldung / address registration and booking
  an appointment is the obvious next step.
- document_checker: compares documents the user has vs. what they need.
  Suggest when the CURRENT TOPIC involves required documents and the user seems
  uncertain about what they have.

Decision rule:
- If CURRENT TOPIC matches one of the agents above → suggest it.
- If CURRENT TOPIC is unrelated (language courses, benefits, general questions) → do not suggest.
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
    query: str = "",
) -> AgentSuggestion | None:
    """Return an AgentSuggestion if a specialist agent clearly fits, else None.

    `query` is the RAG search phrase / stage goal — i.e. what the user was asking
    about. It's the primary signal since session.history doesn't yet include the
    current exchange at call time.
    """
    from core.llm import complete

    recent = history[-6:]
    conv = "\n".join(f"{t.role.upper()}: {t.content}" for t in recent)
    user_msg = (
        f"CURRENT TOPIC: {query or answer.short_answer}\n"
        f"ANSWER GIVEN: {answer.short_answer}\n\n"
        + (f"PRIOR CONVERSATION:\n{conv}\n\n" if conv else "")
        + "Should a specialist agent be offered? Return JSON."
    )

    try:
        result = complete(_SYSTEM, user_msg, json_schema=_SCHEMA)
        if isinstance(result, str):
            result = json.loads(result)
        log.info("agent_suggester decision: %s (query=%r)", result, query)
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
