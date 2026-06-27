"""Track B (Daril) — Grounded answer generation.

Signature fixed (PROTOCOL.md §4.3). The system prompt forbids any claim not in
`sources` and forbids inventing steps/deadlines/documents (constitution #1).
Output is produced in the user's language. Format is calibrated by the LLM to
the complexity of the question (US2/SC-003).
"""
from __future__ import annotations

import json

from core.llm import complete
from core.types import ConversationTurn, Source, StructuredAnswer

SYSTEM = """You are an immigration-guidance assistant for newcomers in Germany.
You answer ONLY from the SOURCES provided. Hard rules:
- Never state a step, deadline, document, fee, or office that is not explicitly
  supported by the SOURCES. If the sources do not cover it, say so in
  `uncertainty` instead of guessing.
- Do not invent procedures. Summarize and translate what the sources say.
- Write every field in the user's language (BCP-47 code given as TARGET_LANG).
- `next_steps` must be concrete imperative actions; `documents_needed` must be
  document names only — nothing else in those arrays.

## Format — calibrate to the question

Simple / conceptual (e.g. "What is Anmeldung?", "What does X mean?",
"Do I need to...?"):
  Put the full answer in `short_answer` (1–3 sentences maximum).
  Leave `next_steps` and `documents_needed` as empty arrays.

Procedural (e.g. "How do I register?", "What steps do I follow?",
"Walk me through..."):
  Put a brief one-sentence summary in `short_answer`.
  List the concrete steps in `next_steps` (imperative, source-grounded).
  List required document names in `documents_needed`.

When in doubt, prefer shorter. Never pad.

Return a JSON object with exactly these keys:
  short_answer (string), next_steps (array of strings),
  documents_needed (array of strings), uncertainty (string or null)."""

# Passed to complete() to trigger JSON mode; keys are also spelled out in SYSTEM.
_SCHEMA = {
    "type": "object",
    "properties": {
        "short_answer": {"type": "string"},
        "next_steps": {"type": "array", "items": {"type": "string"}},
        "documents_needed": {"type": "array", "items": {"type": "string"}},
        "uncertainty": {"type": ["string", "null"]},
    },
    "required": ["short_answer", "next_steps", "documents_needed", "uncertainty"],
}


def _render_sources(sources: list[Source]) -> str:
    blocks = []
    for i, s in enumerate(sources, 1):
        blocks.append(
            f"[S{i}] title: {s.title}\nurl: {s.url}\n"
            f"last_updated: {s.last_updated or 'UNKNOWN'}\n"
            f"language: {s.language}\nexcerpt: {s.excerpt}"
        )
    return "\n\n".join(blocks) if blocks else "(no sources retrieved)"


def _render_history(history: list[ConversationTurn]) -> str:
    recent = history[-6:]  # last 6 turns keeps context without overloading
    lines = []
    for t in recent:
        role = t.role if hasattr(t, "role") else t.get("role", "user")
        content = t.content if hasattr(t, "content") else t.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def generate_answer(
    stage_goal: str,
    user_language: str,
    sources: list[Source],
    slots: dict,
    history: list[ConversationTurn] | None = None,
) -> StructuredAnswer:
    """Produce a StructuredAnswer in `user_language`, grounded only in `sources`."""
    if not sources:
        # No source => no procedural claim (constitution #1). Signal handoff upstream.
        return StructuredAnswer(
            short_answer="",
            uncertainty=(
                "No source pages were found for this question, so no verified "
                "steps can be given."
            ),
        )

    history_section = (
        f"RECENT CONVERSATION:\n{_render_history(history)}\n\n"
        if history
        else ""
    )
    user = (
        f"TARGET_LANG: {user_language}\n"
        f"QUESTION: {stage_goal}\n"
        f"KNOWN USER CONTEXT: {json.dumps(slots, ensure_ascii=False, default=str)}\n\n"
        f"{history_section}"
        f"SOURCES:\n{_render_sources(sources)}\n\n"
        "Produce the JSON answer, grounded only in the SOURCES, written in TARGET_LANG."
    )

    data = complete(SYSTEM, user, json_schema=_SCHEMA)
    if isinstance(data, str):
        data = json.loads(data)
    return StructuredAnswer(
        short_answer=data.get("short_answer", ""),
        next_steps=data.get("next_steps") or [],
        documents_needed=data.get("documents_needed") or [],
        uncertainty=data.get("uncertainty"),
    )
