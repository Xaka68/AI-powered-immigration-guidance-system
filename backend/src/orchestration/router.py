"""Track A (Harsh) — Router (A4).

Maps free text onto the LOADED journey set. Gated by construction: the result is
always intersected with the known journey ids, so the router can never invent a
journey.

Two paths, both semantic — no keyword/entity matching:
- **Primary (LLM):** classifies intent (single best, or multiple only for
  genuinely separable needs) and extracts slots (city, language, urgency).
- **Fallback (no LLM key):** embedding similarity between the message and each
  journey's intent_examples picks the best journey. (Slots are LLM-only.)
"""
from __future__ import annotations

import json

from core.config import settings

# Minimum cosine similarity for the embedding fallback to commit to a journey;
# below this, the message matches nothing (caller shows the welcome screen).
_MIN_SIM = 0.15


def classify(message: str, journeys: dict[str, dict]) -> dict:
    text = (message or "").strip()
    if not text:
        return {"journey_ids": [], "extracted_slots": {}}

    if settings.llm_api_key:
        try:
            return _classify_llm(text, journeys)
        except Exception:
            # Never fail a turn on a flaky model — degrade to embedding matching.
            pass
    return _classify_embeddings(text, journeys)


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


# --- Embedding fallback (semantic, no keyword/entity matching) ---------------------

_journey_emb_cache: dict = {}


def _journey_embeddings(journeys: dict[str, dict]):
    """Embed each journey's (title + intent_examples); cached per journey set."""
    key = tuple(sorted(journeys))
    cached = _journey_emb_cache.get(key)
    if cached is not None:
        return cached
    from retrieval.embeddings import embed_passages

    ids = list(journeys)
    texts = [
        f"{journeys[j].get('title', '')}. " + " ; ".join(journeys[j].get("intent_examples", []))
        for j in ids
    ]
    cached = (ids, embed_passages(texts))
    _journey_emb_cache[key] = cached
    return cached


def _classify_embeddings(message: str, journeys: dict[str, dict]) -> dict:
    """Pick the journey whose intent_examples are most similar to the message.

    Embeddings are L2-normalized, so a dot product is cosine similarity.
    """
    try:
        from retrieval.embeddings import embed_queries

        ids, matrix = _journey_embeddings(journeys)
        q = embed_queries([message])[0]
        sims = [sum(a * b for a, b in zip(q, row)) for row in matrix]
        best = max(range(len(ids)), key=lambda i: sims[i])
        if sims[best] < _MIN_SIM:  # off-topic -> match nothing (welcome screen)
            return {"journey_ids": [], "extracted_slots": {}}
        return {"journey_ids": [ids[best]], "extracted_slots": {}}
    except Exception:
        return {"journey_ids": [], "extracted_slots": {}}
