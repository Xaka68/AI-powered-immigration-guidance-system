"""Goal-understanding agent (ReAct-style reasoning loop).

For an open-ended goal that no curated journey covers, this agent:

  1. UNDERSTANDS first — asks focused clarifying questions (options-first) until it
     knows what the user actually wants/needs, instead of answering too early.
  2. RETRIEVES when ready — searches the indexed Integreat corpus.
  3. FALLS BACK to web search when the corpus is insufficient (pluggable tool;
     `retrieval.web_search` is a stub until a real one is dropped in).
  4. ANSWERS grounded ONLY in what the tools returned — never invents; sets
     uncertainty or hands off when evidence is missing.

Each user turn runs an internal decide -> use-tool -> observe -> decide loop
(up to ``_MAX_STEPS``) before producing a user-facing turn (ask / answer /
handoff). Conversation history lives in ``session.dynamic.history`` (on the
device), so follow-up questions keep context.

Curated journeys remain the trusted gold path — the agent can hand the user into
one via ``suggested_journey_id``.
"""
from __future__ import annotations

import json
import logging

from core.types import (
    ChatRequest,
    ChatResponse,
    DynamicState,
    Option,
    PrivacyReceipt,
    Session,
    Source,
    StructuredAnswer,
)

log = logging.getLogger(__name__)

_HUMAN_CHIP = Option(id="talk_to_human", label="Talk to a counselor")
_MAX_STEPS = 4  # internal reasoning/tool steps per user turn
_MAX_HISTORY = 12  # cap conversation memory kept in the session


def run(
    req: ChatRequest, session: Session, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    """One user turn of the agent. ``session.dynamic`` must already be set."""
    state = session.dynamic
    assert state is not None, "dynamic_journey.run requires session.dynamic"

    user_text = (req.option_id or req.message or "").strip()
    if user_text and state.pending_slot:  # answer to the last clarifying question
        state.facts[state.pending_slot] = user_text
        state.pending_slot = None
    if user_text:
        state.history.append({"role": "user", "content": user_text})
        _cap_history(state)

    language = str(state.facts.get("language") or _detect_language(_last_user(state)))
    city = state.facts.get("city")
    used.add("language")
    if city:
        used.add("city")

    observations: list[dict] = []  # tool results gathered within this turn
    for _ in range(_MAX_STEPS):
        try:
            decision = _decide(state, observations, registry, language)
        except Exception as exc:  # noqa: BLE001
            log.warning("agent decision failed: %s", exc)
            return _handoff_response(
                session, _obs_sources(observations), used,
                "I want to be sure I get this right — let me connect you with a counselor.",
            )

        if decision.get("roadmap"):
            state.roadmap = [str(s) for s in decision["roadmap"]][:8]
        if "current_step_index" in decision:
            state.step_index = _clamp(decision.get("current_step_index"), len(state.roadmap))

        action = str(decision.get("action") or "answer").lower()

        if action == "retrieve":
            observations.append(_corpus_tool(decision, state, city, language))
            continue
        if action == "web_search":
            observations.append(_web_tool(decision, state))
            continue
        if action == "ask":
            return _ask_response(session, decision, registry, used)
        if action == "handoff":
            return _handoff_response(
                session, _obs_sources(observations), used,
                decision.get("assistant_message")
                or "Let me connect you with a counselor who can help.",
            )
        return _answer_response(session, decision, observations, registry, used)

    # Reasoning budget exhausted without a confident answer -> fail safe.
    return _handoff_response(
        session, _obs_sources(observations), used,
        "This is taking a few steps — let me bring in a human counselor to help.",
    )


# ── The agent's brain ─────────────────────────────────────────────────────────────


def _decide(
    state: DynamicState, observations: list[dict], registry: dict[str, dict], language: str
) -> dict:
    from core.llm import complete

    history = "\n".join(f"{h['role']}: {h['content']}" for h in state.history) or "(none)"
    curated = json.dumps(
        [{"id": jid, "title": j["title"]} for jid, j in registry.items()], ensure_ascii=False
    )
    obs_block = _format_observations(observations)

    system = (
        "You are a careful, warm assistant helping a migrant in Germany reach a "
        "goal. Reason step by step about (a) the user's underlying goal, (b) what "
        "details you still need to answer precisely, (c) what you already know, "
        "(d) whether your retrieved evidence is sufficient.\n\n"
        "Each step choose ONE action:\n"
        "- ask: you do NOT yet understand enough to help precisely. Ask ONE "
        "focused clarifying question; set ask_slot and give options (chips) whose "
        "ids are the answer values. Prefer asking over guessing — be thorough.\n"
        "- retrieve: you understand the need; search official Integreat content. "
        "Provide a focused 'query'.\n"
        "- web_search: the retrieved Integreat content does NOT contain enough to "
        "answer. Fall back to the web. Provide a 'query'.\n"
        "- answer: you have enough grounded evidence in the OBSERVATIONS. Write "
        "assistant_message + next_steps + documents_needed grounded ONLY in those "
        "observations. Never invent facts/steps/deadlines. Set uncertainty if partial.\n"
        "- handoff: the case is risky/sensitive, or neither corpus nor web covers it.\n\n"
        "Use CONVERSATION SO FAR for context and handle follow-ups accordingly. "
        "If observations are empty and you have not retrieved yet, retrieve (or ask "
        "first if the goal is vague). Optionally keep a short roadmap (3-6 steps) "
        "with current_step_index to show progress. If a curated journey clearly "
        "fits, set suggested_journey_id. Write user-facing text in the user's language.\n\n"
        "Reply ONLY as JSON: {thought, action, query, assistant_message, ask_slot, "
        "options:[{id,label}], next_steps:[], documents_needed:[], uncertainty, "
        "roadmap:[], current_step_index, suggested_journey_id}."
    )
    user = (
        f"USER LANGUAGE: {language}\n"
        f"CONVERSATION SO FAR:\n{history}\n\n"
        f"WHAT YOU KNOW (facts): {json.dumps(state.facts, ensure_ascii=False)}\n"
        f"ROADMAP: {json.dumps(state.roadmap, ensure_ascii=False)} (step {state.step_index})\n"
        f"CURATED JOURNEYS (suggest only on a direct match): {curated}\n\n"
        f"TOOL OBSERVATIONS THIS TURN:\n{obs_block}\n\n"
        "Decide the next action as JSON."
    )
    result = complete(system, user, json_schema={"type": "object"})
    if isinstance(result, str):
        result = json.loads(result)
    return result


# ── Tools ─────────────────────────────────────────────────────────────────────────


def _corpus_tool(decision: dict, state: DynamicState, city, language: str) -> dict:
    query = str(decision.get("query") or state.goal)
    try:
        from retrieval import search

        hits = search.search(query, city, language, k=6)
    except Exception as exc:  # noqa: BLE001
        log.warning("corpus retrieval failed: %s", exc)
        hits = []
    return {"tool": "corpus", "query": query, "sources": hits}


def _web_tool(decision: dict, state: DynamicState) -> dict:
    query = str(decision.get("query") or state.goal)
    try:
        from retrieval import web_search

        hits = web_search.search(query)
    except Exception as exc:  # noqa: BLE001
        log.warning("web search failed: %s", exc)
        hits = []
    return {"tool": "web", "query": query, "sources": hits}


# ── Response builders ───────────────────────────────────────────────────────────


def _ask_response(
    session: Session, decision: dict, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    state = session.dynamic
    options = _options(decision)
    _append_suggested(options, decision, registry)
    options.append(_HUMAN_CHIP)
    state.pending_slot = decision.get("ask_slot") or None
    message = str(decision.get("assistant_message") or "Could you tell me a bit more?")
    _record_assistant(state, message)
    return _build(session, message, options, answer=None, sources=[], used=used)


def _answer_response(
    session: Session,
    decision: dict,
    observations: list[dict],
    registry: dict[str, dict],
    used: set[str],
) -> ChatResponse:
    state = session.dynamic
    sources = _obs_sources(observations)
    message = str(decision.get("assistant_message") or "Here is what I found.")
    next_steps = [str(s) for s in (decision.get("next_steps") or [])]
    docs = [str(d) for d in (decision.get("documents_needed") or [])]
    uncertainty = decision.get("uncertainty") or None
    answer = StructuredAnswer(
        short_answer=message, next_steps=next_steps,
        documents_needed=docs, uncertainty=uncertainty,
    )
    options: list[Option] = []
    _append_suggested(options, decision, registry)
    options.append(_HUMAN_CHIP)
    state.pending_slot = None
    _record_assistant(state, message)
    return _build(session, message, options, answer=answer, sources=sources, used=used)


def _handoff_response(
    session: Session, sources: list[Source], used: set[str], message: str
) -> ChatResponse:
    from orchestration.handoff_generator import build_summary

    state = session.dynamic
    if state is not None:
        _record_assistant(state, message)
    resp = _build(session, message, [_HUMAN_CHIP], answer=None, sources=sources, used=used)
    resp.requires_handoff = True
    resp.handoff_summary = build_summary(session, sources, None)
    return resp


def _build(
    session: Session,
    message: str,
    options: list[Option],
    answer: StructuredAnswer | None,
    sources: list[Source],
    used: set[str],
) -> ChatResponse:
    state = session.dynamic
    session.journey_id = None
    session.stage_id = "dynamic"
    return ChatResponse(
        journey_id=None,
        stage_id="dynamic",
        assistant_message=message,
        options=options,
        answer=answer,
        sources=sources,
        privacy_receipt=PrivacyReceipt(used_fields=sorted(used), storage="local"),
        roadmap=(state.roadmap if state else []),
        roadmap_step=(state.step_index if state else 0),
        session=session,
    )


# ── Helpers ─────────────────────────────────────────────────────────────────────


def _options(decision: dict) -> list[Option]:
    return [
        Option(id=str(o["id"]), label=str(o["label"]))
        for o in (decision.get("options") or [])
        if isinstance(o, dict) and o.get("id") and o.get("label")
    ]


def _append_suggested(options: list[Option], decision: dict, registry: dict[str, dict]) -> None:
    sid = decision.get("suggested_journey_id")
    if sid in registry and not any(o.id == sid for o in options):
        options.append(Option(id=sid, label=f"Guided help: {registry[sid]['title']}"))


def _obs_sources(observations: list[dict]) -> list[Source]:
    seen: set[str] = set()
    out: list[Source] = []
    for obs in observations:
        for s in obs.get("sources", []):
            if s.url not in seen:
                seen.add(s.url)
                out.append(s)
    return out


def _format_observations(observations: list[dict]) -> str:
    if not observations:
        return "(no tools used yet this turn)"
    blocks = []
    for obs in observations:
        srcs = obs.get("sources", [])
        if not srcs:
            blocks.append(f"[{obs['tool']}] query={obs.get('query')!r}: NO RESULTS")
            continue
        items = "\n".join(
            f"  - {s.title} ({s.url})\n    {(s.excerpt or '')[:400]}" for s in srcs
        )
        blocks.append(f"[{obs['tool']}] query={obs.get('query')!r}:\n{items}")
    return "\n\n".join(blocks)


def _record_assistant(state: DynamicState, message: str) -> None:
    state.history.append({"role": "assistant", "content": message})
    _cap_history(state)


def _cap_history(state: DynamicState) -> None:
    if len(state.history) > _MAX_HISTORY:
        del state.history[:-_MAX_HISTORY]


def _last_user(state: DynamicState) -> str:
    for h in reversed(state.history):
        if h.get("role") == "user":
            return str(h.get("content") or "")
    return state.goal


def _clamp(idx, roadmap_len: int) -> int:
    try:
        i = int(idx)
    except (TypeError, ValueError):
        return 0
    return max(0, min(i, max(roadmap_len - 1, 0)))


def _detect_language(text: str) -> str:
    """Script-based hint (Arabic/Persian -> ar, Cyrillic -> uk, else en);
    an explicit slot language overrides this upstream."""
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F:
            return "ar"
        if 0x0400 <= o <= 0x04FF:
            return "uk"
    return "en"
