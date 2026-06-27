"""Track B (Daril) — Grounded answer generation.

Signature fixed (PROTOCOL.md §4.3). The system prompt forbids any claim not in
`sources` and forbids inventing steps/deadlines/documents (constitution #1).
Output is produced in the user's language.
"""
from __future__ import annotations

import json

from core.llm import complete
from core.types import Source, StructuredAnswer

SYSTEM = """You are an immigration-guidance assistant for newcomers in Germany.
You answer ONLY from the SOURCES provided. Hard rules:
- Never state a step, deadline, document, fee, or office that is not explicitly
  supported by the SOURCES. If the sources do not cover it, say so in
  `uncertainty` instead of guessing.
- Do not invent procedures. Summarize and translate what the sources say.
- Write every field in the user's language (BCP-47 code given as TARGET_LANG).
- Be concrete and brief. `next_steps` are imperative actions; `documents_needed`
  are document names only.
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


def generate_answer(
    stage_goal: str,
    user_language: str,
    sources: list[Source],
    slots: dict,
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

    user = (
        f"TARGET_LANG: {user_language}\n"
        f"STAGE GOAL: {stage_goal}\n"
        f"KNOWN USER CONTEXT (slots): {json.dumps(slots, ensure_ascii=False, default=str)}\n\n"
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
