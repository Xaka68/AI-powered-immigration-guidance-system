"""Track A (Harsh) — Real /chat pipeline (A6).

One turn of the runtime loop (PROTOCOL.md §Runtime Loop):

    route -> graph (escalation / missing slots / transition) ->
    (content stage) retrieval.search + generate_answer + faithfulness.check ->
    assemble ChatResponse + privacy_receipt

Options-first throughout: whenever the next branch is known, we return chips, not
a free-text prompt. The graph is authored; the model only routes and personalizes.

Retrieval (Track B) is called by its fixed signature. Until B lands, a content
stage degrades gracefully (answer with an "integration pending" note) instead of
crashing, so the end-to-end loop is demoable the moment B is wired.
"""
from __future__ import annotations

import logging
import re

from core.types import (
    ChatRequest,
    ChatResponse,
    Option,
    PrivacyReceipt,
    Session,
    Source,
    StructuredAnswer,
)
from orchestration import graph_engine as ge
from orchestration import handoff_generator, router, slot_filler, slot_manager

_HUMAN_OPTION_IDS = {"talk_to_human", "human", "talk_to_counselor", "counselor"}
_HUMAN_CHIP = Option(id="talk_to_human", label="Talk to a counselor")
_MAX_HOPS = 20  # guard against authoring cycles


def run_turn(req: ChatRequest, registry: dict[str, dict]) -> ChatResponse:
    session = (req.session or Session()).model_copy(deep=True)
    used: set[str] = set()

    # Explicit human request, at any point.
    if req.option_id in _HUMAN_OPTION_IDS:
        return _handoff(session, registry, [], used)

    # ── No journey selected yet ────────────────────────────────────────────────
    if not session.journey_id:
        # a) tapped a journey chip from the welcome screen
        if req.option_id and req.option_id in registry:
            session.journey_id = req.option_id
            session.stage_id = ge.first_stage_id(registry[req.option_id])
            return _advance(session, registry, used)

        # b) free text -> route (gated to known journeys)
        if req.message:
            routed = router.classify(req.message, registry)
            session = slot_manager.merge_slots(session, routed["extracted_slots"])
            used.update(routed["extracted_slots"])
            ids = routed["journey_ids"]
            if len(ids) > 1:  # multi-intent: ask which first (options-first)
                chips = [Option(id=i, label=registry[i]["title"]) for i in ids]
                return _respond(
                    session,
                    "You mentioned a few things. Which should we start with?",
                    chips,
                    used,
                )
            if len(ids) == 1:
                session.journey_id = ids[0]
                session.stage_id = ge.first_stage_id(registry[ids[0]])
                return _advance(session, registry, used)
            # No authored journey fits -> Tier 2: grounded one-shot Q&A over the
            # whole Integreat corpus (broad coverage), not a dead-end.
            return _oneshot_qa(req.message, session, registry, used)

        # c) cold start
        return _welcome(session, registry, used)

    # ── Journey in progress: apply this turn's input, then advance ─────────────
    journey = registry[session.journey_id]
    stage = ge.get_stage(journey, session.stage_id or ge.first_stage_id(journey))

    if req.option_id:
        slot = _slot_for_option(stage, req.option_id)
        if slot:
            session = slot_manager.merge_slots(session, {slot: req.option_id})
            used.add(slot)
    elif req.message:
        routed = router.classify(req.message, registry)
        session = slot_manager.merge_slots(session, routed["extracted_slots"])
        used.update(routed["extracted_slots"])

    return _advance(session, registry, used)


# ── Core loop ──────────────────────────────────────────────────────────────────


def _advance(session: Session, registry: dict[str, dict], used: set[str]) -> ChatResponse:
    for _ in range(_MAX_HOPS):
        journey = registry[session.journey_id]
        stage = ge.get_stage(journey, session.stage_id)

        # 1. Escalation exits win.
        target = ge.check_escalation(stage, session.slots)
        if target:
            if _follow(target, session, registry) == "HANDOFF":
                return _handoff(session, registry, [], used)
            continue

        # 2. Missing slots -> ask with chips (human-handoff always offered).
        missing = ge.missing_slots(stage, session.slots)
        if missing:
            used.update(session.slots)
            prompt, chips = slot_filler.chips_for(stage, missing[0])
            return _respond(session, prompt, chips + [_HUMAN_CHIP], used)

        # 3. Content stage -> grounded answer.
        if ge.is_content_stage(stage):
            return _render_content(session, journey, stage, used)

        # 4. Otherwise transition.
        nxt = ge.next_stage(journey, session.stage_id, session.slots)
        _complete(session)
        if nxt is None:
            if stage["type"] == "human_handoff":
                return _handoff(session, registry, [], used)
            return _respond(session, "Is there anything else I can help with?",
                            [_HUMAN_CHIP], used)
        if _follow(nxt, session, registry) == "HANDOFF":
            return _handoff(session, registry, [], used)

    # Cycle guard tripped -> fail safe to a human.
    return _handoff(session, registry, [], used)


def _follow(target: str, session: Session, registry: dict[str, dict]) -> str | None:
    """Mutate session for a stage move or ROUTE. Returns 'HANDOFF' to escalate."""
    if target == "HANDOFF":
        return "HANDOFF"
    if target.startswith("ROUTE:"):
        jid = target.split(":", 1)[1]
        if jid not in registry:
            return "HANDOFF"  # unknown route -> fail safe
        session.journey_id = jid
        session.stage_id = ge.first_stage_id(registry[jid])
        return None
    session.stage_id = target
    return None


def _render_content(session: Session, journey: dict, stage: dict, used: set[str]) -> ChatResponse:
    from retrieval import answer_generator, faithfulness_check, search

    city = session.slots.get("city")
    language = str(session.slots.get("language") or "en")
    if city:
        used.add("city")
    used.add("language")

    try:
        sources = search.search(stage["retrieval_query"], city, language)
        answer = answer_generator.generate_answer(
            stage["goal"], language, sources, session.slots
        )
        answer = faithfulness_check.check(answer, sources)
    except Exception as exc:  # noqa: BLE001 — never 500 a turn on retrieval failure
        # Missing deps/index, model download, network, or NotImplementedError: keep
        # the loop alive and route the user to a human rather than crashing.
        logging.getLogger(__name__).warning("retrieval failed: %s", exc)
        sources = []
        answer = StructuredAnswer(
            short_answer=(
                "I couldn't load grounded information for this step right now. "
                "I can connect you with a human counselor to be safe."
            ),
            uncertainty="Retrieval was unavailable — information could not be verified.",
        )

    _complete(session)
    chips = _stage_chips(stage) + [_HUMAN_CHIP]
    return _respond(session, answer.short_answer, chips, used, answer=answer, sources=sources)


# ── Tier 2: one-shot grounded Q&A (broad Integreat coverage) ─────────────────────


def _oneshot_qa(
    question: str, session: Session, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    """Answer a free-text question directly from the whole indexed corpus when no
    authored journey fits — so the system covers Integreat's breadth, not just the
    ~9 guided flows. Still options-first: the answer carries suggested-journey
    chips + a human exit. Never fabricates: no sources -> offer journeys/handoff.
    """
    from retrieval import answer_generator, faithfulness_check, search

    language = str(session.slots.get("language") or _detect_language(question))
    city = session.slots.get("city")
    if city:
        used.add("city")
    used.add("language")
    session.journey_id = None
    session.stage_id = "qa"

    try:
        sources = search.search(question, city, language, k=5)
        if not sources:
            return _welcome(
                session, registry, used,
                "I couldn't find that in the official information yet. Here's what I "
                "can guide you through — or I can connect you with a counselor.",
            )
        answer = answer_generator.generate_answer(question, language, sources, session.slots)
        answer = faithfulness_check.check(answer, sources)
    except Exception as exc:  # noqa: BLE001 — never 500 a turn on retrieval failure
        logging.getLogger(__name__).warning("tier-2 QA failed: %s", exc)
        return _welcome(
            session, registry, used,
            "I couldn't load that right now — here's what I can guide you through.",
        )

    chips = _suggest_journeys(question, registry) + [_HUMAN_CHIP]
    return _respond(session, answer.short_answer, chips, used, answer=answer, sources=sources)


def _suggest_journeys(question: str, registry: dict[str, dict], limit: int = 3) -> list[Option]:
    """Loosely related journeys (title/description/intent overlap) to let the user
    pivot from a one-shot answer into a guided flow. Empty when nothing relates."""
    q_tokens = {t for t in re.findall(r"\w+", question.lower()) if len(t) >= 4}
    scored: list[tuple[int, str, str]] = []
    for jid, j in registry.items():
        hay = " ".join(
            [j.get("title", ""), j.get("description", ""), *j.get("intent_examples", [])]
        ).lower()
        overlap = len(q_tokens & set(re.findall(r"\w+", hay)))
        if overlap:
            scored.append((overlap, jid, j["title"]))
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [Option(id=jid, label=title) for _, jid, title in scored[:limit]]


def _detect_language(text: str) -> str:
    """Cheap script-based language hint so a non-Latin question is answered in
    kind. Ambiguous Arabic-script defaults to 'ar'; Cyrillic -> 'uk'; else 'en'.
    An explicit slot language (from the router/LLM) always takes precedence."""
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F:  # Arabic / Persian script
            return "ar"
        if 0x0400 <= o <= 0x04FF:  # Cyrillic
            return "uk"
    return "en"


# ── Response builders ───────────────────────────────────────────────────────────


def _welcome(session: Session, registry: dict[str, dict], used: set[str], msg: str | None = None) -> ChatResponse:
    session.stage_id = "orientation"
    chips = [Option(id=jid, label=j["title"]) for jid, j in registry.items()]
    chips.append(_HUMAN_CHIP)
    message = msg or "I can help you step by step. What would you like to do first?"
    return _respond(session, message, chips, used)


def _handoff(session: Session, registry: dict[str, dict], sources: list[Source], used: set[str]) -> ChatResponse:
    journey = registry.get(session.journey_id) if session.journey_id else None
    summary = handoff_generator.build_summary(session, sources, journey)
    resp = _respond(
        session,
        "I'll connect you with a human counselor. Please review and edit this "
        "summary before you share it.",
        [],
        used,
        sources=sources,
    )
    resp.requires_handoff = True
    resp.handoff_summary = summary
    return resp


def _respond(
    session: Session,
    assistant: str,
    options: list[Option],
    used: set[str],
    answer: StructuredAnswer | None = None,
    sources: list[Source] | None = None,
) -> ChatResponse:
    return ChatResponse(
        journey_id=session.journey_id,
        stage_id=session.stage_id,
        assistant_message=assistant,
        options=options,
        answer=answer,
        sources=sources or [],
        privacy_receipt=PrivacyReceipt(
            used_fields=sorted(f for f in used if f in session.slots),
            stored_fields=[],
            storage="local",
            human_shared=False,
        ),
        session=session,
    )


# ── Small helpers ───────────────────────────────────────────────────────────────


def _slot_for_option(stage: dict, option_id: str) -> str | None:
    for option_set in stage.get("option_sets", []):
        if any(o["id"] == option_id for o in option_set["options"]):
            return option_set["slot"]
    return None


def _stage_chips(stage: dict) -> list[Option]:
    """Surface a content stage's option_sets as 'what next' chips (edge cases)."""
    chips: list[Option] = []
    for option_set in stage.get("option_sets", []):
        chips.extend(Option(id=o["id"], label=o["label"]) for o in option_set["options"])
    return chips


def _complete(session: Session) -> None:
    if session.stage_id and session.stage_id not in session.completed_stages:
        session.completed_stages.append(session.stage_id)
