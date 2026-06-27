"""Adapter between the pipeline/contract and the LangGraph agent (agent_graph).

Keeps the ``run(req, session, registry, used)`` interface the pipeline expects.
It manages the conversation memory in ``session.dynamic.history`` (on the device),
calls the LangGraph agent for one turn, and maps the agent's result back onto the
ChatResponse contract (options-first chips, grounded answer, sources, handoff).

Conversation isolation: history travels in the session, so a new chat (fresh
session) starts with empty memory — no bleed between conversations.
"""
from __future__ import annotations

import logging

from core.types import (
    ChatRequest,
    ChatResponse,
    Option,
    PrivacyReceipt,
    Session,
    Source,
    StructuredAnswer,
)

log = logging.getLogger(__name__)

_HUMAN_CHIP = Option(id="talk_to_human", label="Talk to a counselor")
_MAX_HISTORY = 16  # cap conversation memory kept in the session


def run(
    req: ChatRequest, session: Session, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    """One agent turn. ``session.dynamic`` must already be set."""
    state = session.dynamic
    assert state is not None, "dynamic_journey.run requires session.dynamic"

    user_text = (req.option_id or req.message or "").strip()
    if user_text:
        state.history.append({"role": "user", "content": user_text})
        _cap(state)

    language = str(session.slots.get("language") or _detect_language(user_text or state.goal))
    city = session.slots.get("city")
    used.add("language")
    if city:
        used.add("city")

    from orchestration import agent_graph

    try:
        result = agent_graph.run_agent(
            history=state.history, city=city, language=language, registry=registry
        )
    except Exception as exc:  # noqa: BLE001 — never 500 a turn on agent failure
        log.warning("agent failed: %s", exc)
        return _handoff(
            session, [], used,
            "I want to be sure I get this right — let me connect you with a counselor.",
        )

    message = str(result.get("message") or "Let's continue.")
    state.history.append({"role": "assistant", "content": message})
    _cap(state)
    session.dynamic = state
    session.journey_id = None
    session.stage_id = "dynamic"

    sources: list[Source] = _compact_sources(result.get("sources") or [])

    if result.get("kind") == "handoff":
        return _handoff(session, sources, used, message or "Let me bring in a counselor.")

    options: list[Option] = [
        Option(id=str(label), label=str(label)) for label in (result.get("options") or [])
    ]
    sj = result.get("suggested_journey")
    if sj in registry and not any(o.id == sj for o in options):
        options.append(Option(id=sj, label=f"Guided help: {registry[sj]['title']}"))
    options.append(_HUMAN_CHIP)

    answer = None
    if result.get("kind") == "answer":
        next_steps = [str(s) for s in (result.get("next_steps") or [])]
        docs = [str(d) for d in (result.get("documents_needed") or [])]
        uncertainty = result.get("uncertainty") or None
        if next_steps or docs or uncertainty:
            # short_answer stays empty: the message is shown as the chat bubble, so
            # repeating it here would duplicate it in the answer card.
            answer = StructuredAnswer(
                short_answer="", next_steps=next_steps,
                documents_needed=docs, uncertainty=uncertainty,
            )

    return _build(session, message, options, answer, sources, used)


# ── Response builders ───────────────────────────────────────────────────────────


def _handoff(
    session: Session, sources: list[Source], used: set[str], message: str
) -> ChatResponse:
    from orchestration.handoff_generator import build_summary

    resp = _build(session, message, [_HUMAN_CHIP], None, sources, used)
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
        session=session,
    )


# ── Helpers ─────────────────────────────────────────────────────────────────────


def _compact_sources(sources: list[Source], limit: int = 5) -> list[Source]:
    """Dedupe by URL and strip excerpts — the UI shows sources as compact links,
    not long text. (The agent already used the full text while reasoning.)"""
    seen: set[str] = set()
    out: list[Source] = []
    for s in sources:
        if not s.url or s.url in seen:
            continue
        seen.add(s.url)
        out.append(
            Source(title=s.title or s.url, url=s.url,
                   last_updated=s.last_updated, language=s.language, excerpt="")
        )
        if len(out) >= limit:
            break
    return out


def _cap(state) -> None:
    if len(state.history) > _MAX_HISTORY:
        del state.history[:-_MAX_HISTORY]


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
