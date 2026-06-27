"""Dynamic journey planner (hybrid).

For an open-ended goal that no curated journey covers, build a personalized,
SOURCE-GROUNDED plan and walk the user through it one step at a time — instead of
dumping a single RAG answer.

Hybrid: the LLM maintains a short visible roadmap (so the user sees progress) AND
decides the next interaction each turn (so it stays adaptive). It is dynamic in
*shape* but never invents procedure: every factual step must be supported by the
retrieved Integreat content; if it isn't, we say so and offer a human. Curated
journeys remain the trusted "gold path" — the planner can hand the user into one
via ``suggested_journey_id``.

State (goal, roadmap, step, learned facts) lives in ``session.dynamic`` on the
device — same privacy posture as the rest of the wallet.
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


def run(
    req: ChatRequest, session: Session, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    """One turn of a dynamic journey. ``session.dynamic`` must already be set."""
    state = session.dynamic
    assert state is not None, "dynamic_journey.run requires session.dynamic"

    user_input = (req.option_id or req.message or "").strip()
    # Record the answer to the question we asked last turn (options-first slots).
    if user_input and state.pending_slot:
        state.facts[state.pending_slot] = user_input

    language = str(state.facts.get("language") or _detect_language(state.goal))
    city = state.facts.get("city")
    if city:
        used.add("city")
    used.add("language")

    # Retrieve grounding for the goal + the current step (+ the user's latest input).
    step_hint = (
        state.roadmap[state.step_index]
        if state.roadmap and 0 <= state.step_index < len(state.roadmap)
        else ""
    )
    query = " ".join(p for p in (state.goal, step_hint, user_input) if p).strip()
    try:
        from retrieval import search

        sources = search.search(query, city, language, k=6)
    except Exception as exc:  # noqa: BLE001
        log.warning("dynamic retrieval failed: %s", exc)
        sources = []

    # Plan/step with the LLM (structured, grounded). Failure -> safe handoff.
    try:
        turn = _plan_turn(state, sources, user_input, language, registry)
    except Exception as exc:  # noqa: BLE001
        log.warning("dynamic planner failed: %s", exc)
        return _handoff_response(
            session, sources, used,
            "I want to be sure I get this right — let me connect you with a counselor.",
        )

    # Update dynamic state from the turn.
    if turn.get("roadmap"):
        state.roadmap = [str(s) for s in turn["roadmap"]][:8]
    max_idx = max(len(state.roadmap) - 1, 0)
    state.step_index = max(0, min(int(turn.get("current_step_index", state.step_index)), max_idx))
    state.pending_slot = (turn.get("ask_slot") or None)
    session.dynamic = state
    session.journey_id = None
    session.stage_id = "dynamic"

    # Assemble the response (options-first; always a human exit).
    options = [
        Option(id=str(o["id"]), label=str(o["label"]))
        for o in (turn.get("options") or [])
        if isinstance(o, dict) and o.get("id") and o.get("label")
    ]
    suggested = turn.get("suggested_journey_id")
    if suggested in registry:
        options.append(Option(id=suggested, label=f"Guided help: {registry[suggested]['title']}"))
    options.append(_HUMAN_CHIP)

    next_steps = [str(s) for s in (turn.get("next_steps") or [])]
    docs = [str(d) for d in (turn.get("documents_needed") or [])]
    uncertainty = turn.get("uncertainty") or None
    message = str(turn.get("assistant_message") or "Let's keep going.")
    answer = None
    if next_steps or docs or uncertainty:
        answer = StructuredAnswer(
            short_answer=message, next_steps=next_steps,
            documents_needed=docs, uncertainty=uncertainty,
        )

    needs_handoff = bool(turn.get("needs_handoff"))
    resp = ChatResponse(
        journey_id=None,
        stage_id="dynamic",
        assistant_message=message,
        options=options,
        answer=answer,
        sources=sources,
        privacy_receipt=PrivacyReceipt(used_fields=sorted(used), storage="local"),
        requires_handoff=needs_handoff,
        roadmap=state.roadmap,
        roadmap_step=state.step_index,
        session=session,
    )
    if needs_handoff:
        from orchestration.handoff_generator import build_summary

        resp.handoff_summary = build_summary(session, sources, None)
    return resp


def _plan_turn(
    state: DynamicState,
    sources: list[Source],
    user_input: str,
    language: str,
    registry: dict[str, dict],
) -> dict:
    """One structured LLM turn: maintain the roadmap and decide the next step."""
    from core.llm import complete

    src_block = "\n\n".join(
        f"[{i + 1}] {s.title} ({s.url})\n{(s.excerpt or '')[:600]}"
        for i, s in enumerate(sources)
    ) or "(no sources found)"
    curated = json.dumps(
        [{"id": jid, "title": j["title"]} for jid, j in registry.items()],
        ensure_ascii=False,
    )

    system = (
        "You are a patient guide helping a migrant in Germany reach a goal, ONE "
        "step at a time. Do NOT dump everything at once — walk them through it, "
        "asking a clarifying question when the next step depends on their "
        "situation, and offering tappable options.\n"
        "STRICT GROUNDING: base every factual step, document, deadline, or "
        "requirement ONLY on the SOURCES provided. Never invent procedures. If the "
        "sources do not cover the next step, set needs_handoff=true and explain.\n"
        "Maintain a short roadmap (3-6 steps) toward the goal and advance "
        "current_step_index as steps complete.\n"
        "Prefer options over free text. When you ask something, set ask_slot to a "
        "short snake_case key and give options whose ids are the answer values.\n"
        "If a curated journey directly matches the goal, set suggested_journey_id "
        "to its id so the user can switch to the trusted guided flow.\n"
        "Be warm and plain-language, and write assistant_message in the user's "
        "language.\n"
        "Reply ONLY as JSON with keys: roadmap (list of short step titles), "
        "current_step_index (int), assistant_message (string), ask_slot (string "
        "or null), options (list of {id,label}), next_steps (list of strings), "
        "documents_needed (list of strings), needs_handoff (bool), "
        "suggested_journey_id (string or null), goal_complete (bool), "
        "uncertainty (string or null)."
    )
    user = (
        f"USER LANGUAGE: {language}\n"
        f"GOAL: {state.goal}\n"
        f"KNOWN ABOUT USER: {json.dumps(state.facts, ensure_ascii=False)}\n"
        f"CURRENT ROADMAP: {json.dumps(state.roadmap, ensure_ascii=False)}\n"
        f"CURRENT STEP INDEX: {state.step_index}\n"
        f"USER'S LATEST INPUT: {user_input or '(none — first turn)'}\n"
        f"CURATED JOURNEYS (suggest only on a direct match): {curated}\n\n"
        f"SOURCES:\n{src_block}\n\n"
        "Produce the next turn as JSON."
    )
    result = complete(system, user, json_schema={"type": "object"})
    if isinstance(result, str):
        result = json.loads(result)
    return result


def _handoff_response(
    session: Session, sources: list[Source], used: set[str], message: str
) -> ChatResponse:
    from orchestration.handoff_generator import build_summary

    session.journey_id = None
    session.stage_id = "dynamic"
    state = session.dynamic
    return ChatResponse(
        journey_id=None,
        stage_id="dynamic",
        assistant_message=message,
        options=[_HUMAN_CHIP],
        answer=None,
        sources=sources,
        privacy_receipt=PrivacyReceipt(used_fields=sorted(used), storage="local"),
        requires_handoff=True,
        handoff_summary=build_summary(session, sources, None),
        roadmap=(state.roadmap if state else []),
        roadmap_step=(state.step_index if state else 0),
        session=session,
    )


def _detect_language(text: str) -> str:
    """Script-based language hint (Arabic/Persian -> ar, Cyrillic -> uk, else en);
    an explicit slot language always overrides this upstream."""
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F:
            return "ar"
        if 0x0400 <= o <= 0x04FF:
            return "uk"
    return "en"
