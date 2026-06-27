"""Context-gathering engine — Phase 2, US1.

run_turn() decides whether to ask a clarifying question or hand off to RAG.
The LLM sees the full conversation history (token-capped on the client) so it
never asks for information the user already shared.

System prompt written with Lyra discipline: gather context naturally, one
focused question at a time, decide when it knows enough, reply in user's language.
"""
from __future__ import annotations

import json
import logging

from core.types import ConversationTurn

log = logging.getLogger(__name__)

# T008 — Lyra-optimised system prompt for context gathering (GPT-5.5 / o-series).
_SYSTEM = """\
You are the context-gathering intelligence of Integreat Compass — a calm, trusted \
assistant helping migrants and refugees navigate life in Germany.

## YOUR ONLY JOB
Before every response, silently work through this checklist:
1. What does this person actually want to achieve?
2. What city or region are they in? (matters for offices, deadlines, local rules)
3. What is their residence/visa status? (changes eligibility for many services)
4. Is there anything else missing that would meaningfully change the answer?

If you can answer all four confidently from the conversation so far → output the ANSWER shape.
If any answer is "unknown and it matters" → output the ASK shape with ONE focused question.

## OUTPUT RULES (non-negotiable)
- You MUST output valid JSON. No preamble, no explanation, no markdown — raw JSON only.
- Choose exactly one of the two shapes below. Never mix them.
- If you are uncertain which shape to use, default to ASK.

## SHAPES

Ask shape — when you need one more piece of context:
{
  "action": "ask",
  "question": "<warm, natural question in the user's language>",
  "options": ["<option A>", "<option B>", "<option C>"]
}
options is optional — include 3-4 short choices only when the answer is clearly one \
of a few known values. Omit it for open-ended answers.

Answer shape — when you know enough to search:
{
  "action": "answer",
  "query_for_rag": "<specific English search phrase for a German immigration knowledge base>",
  "facts_extracted": {
    "city": "<city if known, else omit key>",
    "language": "<BCP-47 code of user's language>",
    "visa_type": "<if known>",
    "goal": "<one-line summary of what they need>"
  }
}
query_for_rag must be a precise English phrase (e.g. "Anmeldung address registration \
Munich first time"). Include city and topic. facts_extracted captures everything \
useful learned across the full conversation.

## LANGUAGE
Always reply in the user's language. If they write in Arabic → ask in Arabic. \
German → German. Ukrainian, Farsi, Turkish → match it exactly.

## TONE
Warm and direct — a knowledgeable friend, not a government form. \
One question at a time. Never ask for something already shared in the conversation.

## EXAMPLES

User: "I need help"
→ {"action": "ask", "question": "Of course! What do you need help with — housing, registration, healthcare, work, or something else?", "options": ["Housing", "Registration (Anmeldung)", "Healthcare", "Work / job"]}

User: "How do I register my address in Munich?"
→ {"action": "answer", "query_for_rag": "Anmeldung address registration Munich first time", "facts_extracted": {"city": "Munich", "language": "en", "goal": "register address for the first time"}}

User: "أريد العثور على شقة"
→ {"action": "ask", "question": "بالتأكيد! هل تبحث عن شقة في مدينة معينة؟", "options": ["ميونخ", "برلين", "هامبورغ", "مدينة أخرى"]}
"""


def run_turn(
    message: str,
    history: list[ConversationTurn],
    facts: dict,
    registry: dict,  # reserved for future domain-hint enrichment
) -> dict:
    """
    Returns one of:
      {"action": "ask",    "question": str, "options": list[str]}
      {"action": "answer", "query_for_rag": str, "facts_extracted": dict}
    Falls back to a generic clarifying question on any error.
    """
    from core.llm import complete

    msgs = _build_messages(message, history)
    system = _system_with_facts(facts)

    try:
        result = complete(system, json_schema={}, messages=msgs)
        if isinstance(result, str):
            result = json.loads(result)
        action = result.get("action")
        if action == "ask" and result.get("question"):
            return {
                "action": "ask",
                "question": result["question"],
                "options": result.get("options") or [],
            }
        if action == "answer" and result.get("query_for_rag"):
            return {
                "action": "answer",
                "query_for_rag": result["query_for_rag"],
                "facts_extracted": result.get("facts_extracted") or {},
            }
        log.warning("context_engine: unexpected LLM shape: %s", result)
    except Exception as exc:
        log.warning("context_engine error: %s", exc)
        raise  # let pipeline catch and fall back to handoff

    # Malformed JSON that passed the try block — ask a safe generic question.
    return {
        "action": "ask",
        "question": "Could you tell me a bit more about your situation and what you need help with?",
        "options": [],
    }


def _build_messages(message: str, history: list[ConversationTurn]) -> list[dict]:
    msgs = [{"role": t.role, "content": t.content} for t in history]
    msgs.append({"role": "user", "content": message})
    return msgs


def _system_with_facts(facts: dict) -> str:
    if not facts:
        return _SYSTEM
    known = "; ".join(f"{k}: {v}" for k, v in facts.items() if v)
    if not known:
        return _SYSTEM
    return _SYSTEM + f"\n\n## Already known about this person\n{known}"
