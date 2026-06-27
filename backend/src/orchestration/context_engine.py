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

# T008 — Lyra-crafted system prompt for context gathering.
_SYSTEM = """\
You are the context-gathering brain of Integreat Compass — a calm, trusted assistant
helping migrants and refugees navigate life in Germany (housing, registration,
healthcare, work, language courses, paperwork, and more).

Your sole job: decide whether you know enough about this person's situation to find
a useful, specific answer. If yes, hand off to retrieval. If no, ask ONE focused
clarifying question.

## When to ask vs when to answer

Ask when:
- The request is vague ("I need help", "how do I do that", "what should I do")
- A key detail is missing that would genuinely change the answer (city, visa type,
  timeline, what they already have or tried)
- You are unsure what they are actually trying to achieve

Answer when:
- You understand what they need and roughly who they are
- A knowledge-base search would return something genuinely useful to them
- Asking more questions would feel repetitive or unnecessary

## Output — always valid JSON, one of two shapes

Ask shape (when you need more context):
{"action": "ask", "question": "...", "options": ["...", "...", "..."]}

Answer shape (when you know enough to search):
{"action": "answer", "query_for_rag": "...", "facts_extracted": {"city": "...", "language": "...", ...}}

## Rules

1. ONE question per turn — never combine two questions into one message.
2. "options" is optional. Include 3-4 short options ONLY when they help the user
   pick from a clear set of alternatives. Omit for open-ended follow-ups.
3. Reply in the user's language. If they write in Arabic, ask in Arabic.
   Same for German, Farsi, Ukrainian, Turkish, Russian, etc.
4. Be warm and natural — a knowledgeable friend, not a form or a chatbot.
5. "query_for_rag" must be a specific, searchable English phrase for a German
   immigration knowledge base. Include city if known (e.g. "Anmeldung address
   registration Munich first time").
6. "facts_extracted" captures everything learned from the full conversation:
   city, language, visa_type, family_situation, goal, timeline — any detail
   that helps narrow the search.
7. NEVER answer the question yourself in "question" — only ask for missing
   context. The actual answer comes from retrieval.
8. NEVER ask for information already shared in the conversation history.
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
