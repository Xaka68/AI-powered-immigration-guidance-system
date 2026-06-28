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

from core.config import settings
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
from orchestration import dynamic_journey
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

    # Tapping a journey chip enters that curated journey — works from the welcome
    # screen OR from a dynamic journey, so the user can "land" on the trusted gold
    # path when the planner suggests it.
    if req.option_id and req.option_id in registry:
        session.dynamic = None
        session.journey_id = req.option_id
        session.stage_id = ge.first_stage_id(registry[req.option_id])
        return _advance(session, registry, used)

    # Continue an in-progress dynamic journey.
    if session.dynamic is not None and not session.journey_id:
        return dynamic_journey.run(req, session, registry, used)

    # ── No journey selected yet ────────────────────────────────────────────────
    if not session.journey_id:
        # AGENT-FIRST: any free-text goal goes to the reasoning agent, which
        # understands the need, clarifies, retrieves, and answers. Curated
        # journeys are the trusted gold path the agent routes INTO (via a
        # suggestion chip) or that the user taps directly from the welcome screen —
        # NOT a router gate that pre-empts the agent with a rigid menu.
        if req.message:
            session.dynamic = DynamicState(goal=req.message)
            return dynamic_journey.run(req, session, registry, used)

        # Cold start: welcome + quick curated entry points.
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
            external_llm=settings.llm_external,
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
