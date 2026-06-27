"""Track A (Harsh) — Router (A4).

Maps free text onto the LOADED journey set. Gated by construction: the result is
always intersected with the known journey ids, so the router can never invent a
journey. Returns ranked `journey_ids` (multi-intent) plus any `extracted_slots`
(city, language, urgency, ...).

Uses the LLM when an LLM_API_KEY is configured; otherwise falls back to a
deterministic keyword matcher over each journey's `intent_examples`, so the
pipeline runs offline during development and upgrades transparently with a key.
"""
from __future__ import annotations

import json
import re

from core.config import settings

# Minimal, language-agnostic slot cues for the offline fallback. The LLM path
# extracts these far better; this just keeps the dev loop working without a key.
_CITY_CUES = {"munich": "Munich", "münchen": "Munich", "berlin": "Berlin", "hamburg": "Hamburg"}
_URGENCY_CUES = ("urgent", "emergency", "homeless", "no place", "tonight", "notfall", "dringend")
_LANG_CUES = {
    "arabic": "ar", "عرب": "ar", "farsi": "fa", "persian": "fa", "فارسی": "fa",
    "ukrainian": "uk", "українськ": "uk", "turkish": "tr", "türk": "tr", "english": "en",
}


def classify(message: str, journeys: dict[str, dict]) -> dict:
    text = (message or "").strip()
    if not text:
        return {"journey_ids": [], "extracted_slots": {}}

    if settings.llm_api_key:
        try:
            return _classify_llm(text, journeys)
        except Exception:
            # Never fail a turn on a flaky model — degrade to keyword matching.
            pass
    return _classify_keywords(text, journeys)


def _classify_llm(message: str, journeys: dict[str, dict]) -> dict:
    from core.llm import complete

    catalog = [
        {"id": jid, "title": j["title"], "intent_examples": j.get("intent_examples", [])}
        for jid, j in journeys.items()
    ]
    system = (
        "You route a migrant's message to known guidance journeys. "
        "Choose ONLY from the provided journey ids — never invent one. "
        "Return the SINGLE most relevant journey id in almost all cases — pick the "
        "one best next step for the user's situation, not every loosely-related topic. "
        "Return MULTIPLE ids ONLY when the message clearly contains two or more "
        "distinct, separable needs (e.g. 'Kita AND a German course'); then rank them "
        "most important first. A single situation described with context (e.g. "
        "'I found a room, what next?') is ONE intent, not several. "
        "Also extract slots if clearly present: city, language (ISO code), urgency "
        "('high' only if urgent/crisis). "
        'Reply as JSON: {"journey_ids": [...], "extracted_slots": {...}}.'
    )
    user = f"Journeys:\n{json.dumps(catalog, ensure_ascii=False)}\n\nMessage: {message}"
    result = complete(system, user, json_schema={"type": "object"})
    if isinstance(result, str):
        result = json.loads(result)

    known = set(journeys)
    ids = [j for j in result.get("journey_ids", []) if j in known]  # gate
    slots = {k: v for k, v in (result.get("extracted_slots") or {}).items() if v}
    return {"journey_ids": ids, "extracted_slots": slots}


def _classify_keywords(message: str, journeys: dict[str, dict]) -> dict:
    low = message.lower()
    scored: list[tuple[int, str]] = []
    for jid, journey in journeys.items():
        score = 0
        for example in journey.get("intent_examples", []):
            for token in re.findall(r"\w+", example.lower()):
                if len(token) >= 3 and token in low:
                    score += 1
        if score:
            scored.append((score, jid))
    scored.sort(key=lambda s: (-s[0], s[1]))
    # Keep only the strongest match(es): a dominant single journey wins, but
    # genuinely co-equal intents (e.g. "Kita and Deutschkurs") both surface.
    top = scored[0][0] if scored else 0
    journey_ids = [jid for sc, jid in scored if sc == top]

    extracted: dict[str, object] = {}
    for cue, city in _CITY_CUES.items():
        if cue in low:
            extracted["city"] = city
            break
    for cue, lang in _LANG_CUES.items():
        if cue in low:
            extracted["language"] = lang
            break
    if any(cue in low for cue in _URGENCY_CUES):
        extracted["urgency"] = "high"

    return {"journey_ids": journey_ids, "extracted_slots": extracted}
