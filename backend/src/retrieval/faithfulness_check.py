"""Track B (Daril) — Faithfulness pass.

Drops/flags any next_step or document not supported by the sources, and sets
`uncertainty` when freshness is missing. Uses an LLM verifier when configured;
otherwise applies the deterministic freshness rule so B5 still adds value
without an LLM endpoint. Signature fixed (PROTOCOL.md §4.3).
"""
from __future__ import annotations

import json

from core.types import Source, StructuredAnswer

_VERIFY_SYSTEM = """You are a strict fact-checker. Given SOURCES and a candidate
answer, keep each item in `next_steps` and `documents_needed` ONLY if it is
explicitly supported by the SOURCES; otherwise drop it. Never add new items. Keep
wording and language unchanged for retained items.
Return a JSON object with exactly these keys:
  short_answer (string), next_steps (array of strings),
  documents_needed (array of strings), uncertainty (string or null)."""

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


def _freshness_note(sources: list[Source]) -> str | None:
    if not sources:
        return "No sources were available to verify this answer."
    if any(not s.last_updated for s in sources):
        return "Some sources have no verifiable last-updated date; please confirm currency."
    return None


def _append_uncertainty(existing: str | None, note: str | None) -> str | None:
    if not note:
        return existing
    if not existing:
        return note
    return existing if note in existing else f"{existing} {note}"


def check(answer: StructuredAnswer, sources: list[Source]) -> StructuredAnswer:
    """Return a faithfulness-filtered copy of `answer`."""
    fresh_note = _freshness_note(sources)

    try:
        from core.llm import complete

        srcs = "\n\n".join(
            f"[S{i}] {s.title} ({s.last_updated or 'UNKNOWN'})\n{s.excerpt}"
            for i, s in enumerate(sources, 1)
        )
        user = (
            f"SOURCES:\n{srcs}\n\nCANDIDATE ANSWER (JSON):\n"
            f"{answer.model_dump_json()}\n\nReturn the filtered JSON object."
        )
        data = complete(_VERIFY_SYSTEM, user, json_schema=_SCHEMA)
        if isinstance(data, str):
            data = json.loads(data)
        return StructuredAnswer(
            short_answer=data.get("short_answer", answer.short_answer),
            next_steps=data.get("next_steps") or [],
            documents_needed=data.get("documents_needed") or [],
            uncertainty=_append_uncertainty(data.get("uncertainty"), fresh_note),
        )
    except Exception:
        # No LLM available: still enforce the freshness guardrail deterministically.
        return StructuredAnswer(
            short_answer=answer.short_answer,
            next_steps=answer.next_steps,
            documents_needed=answer.documents_needed,
            uncertainty=_append_uncertainty(answer.uncertainty, fresh_note),
        )
