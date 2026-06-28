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

from core.config import settings
from core.types import (
    AnswerSection,
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


def _prepare(
    req: ChatRequest, session: Session, used: set[str]
) -> tuple["DynamicState", str | None, str]:
    """Shared setup for both the blocking and streaming agent paths: record the
    user's turn, resolve+persist the language, and read the city."""
    state = session.dynamic
    assert state is not None, "dynamic_journey requires session.dynamic"

    user_text = (req.option_id or req.message or "").strip()
    if user_text:
        state.history.append({"role": "user", "content": user_text})
        _cap(state)

    # Detect the user's language once, then persist it so short follow-ups
    # ("yes", "Munich") don't get misread as English mid-conversation.
    language = session.slots.get("language")
    if not language:
        language = _detect_language(user_text or state.goal)
        session.slots["language"] = language
    language = str(language)
    city = session.slots.get("city")
    used.add("language")
    if city:
        used.add("city")
    return state, city, language


def run(
    req: ChatRequest, session: Session, registry: dict[str, dict], used: set[str]
) -> ChatResponse:
    """One agent turn (blocking). ``session.dynamic`` must already be set."""
    state, city, language = _prepare(req, session, used)
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
    return _result_to_response(result, session, state, registry, used)


def run_stream(
    req: ChatRequest, session: Session, registry: dict[str, dict], used: set[str]
):
    """One agent turn (streaming). Yields the agent's step events as they happen,
    then a final ``{"type": "response", "data": ChatResponse}``."""
    state, city, language = _prepare(req, session, used)
    from orchestration import agent_graph

    result: dict | None = None
    try:
        for ev in agent_graph.stream_agent(
            history=state.history, city=city, language=language, registry=registry
        ):
            if ev.get("type") == "final":
                result = ev["result"]
            else:
                yield ev
    except Exception as exc:  # noqa: BLE001 — never 500 mid-stream
        log.warning("agent stream failed: %s", exc)
        resp = _handoff(
            session, [], used,
            "I want to be sure I get this right — let me connect you with a counselor.",
        )
        yield {"type": "response", "data": resp}
        return

    if result is None:
        result = {"kind": "handoff",
                  "message": "Let me connect you with a counselor who can help.",
                  "sources": []}
    yield {"type": "response",
           "data": _result_to_response(result, session, state, registry, used)}


def _result_to_response(
    result: dict, session: Session, state: "DynamicState",
    registry: dict[str, dict], used: set[str],
) -> ChatResponse:
    """Turn an agent result dict into a ChatResponse (shared by run + run_stream)."""
    message = str(result.get("message") or "Let's continue.")
    state.history.append({"role": "assistant", "content": message})
    _cap(state)
    session.dynamic = state
    session.journey_id = None
    session.stage_id = "dynamic"

    sources: list[Source] = _compact_sources(result.get("sources") or [])

    if result.get("kind") == "handoff":
        return _handoff(session, sources, used, message or "Let me bring in a counselor.")

    # Chips: ask_user options, or (after an answer) the agent's proactive follow-up
    # proposals — so the user always has an easy next step to go deeper. Drop any
    # counselor-like proposal (the system adds the single counselor chip itself) and
    # dedupe, so we never show two "talk to a counselor" buttons.
    chip_labels = result.get("options") or result.get("follow_ups") or []
    options: list[Option] = []
    seen: set[str] = set()
    for label in chip_labels:
        text = str(label).strip()
        if not text or _is_counselor(text) or text in seen:
            continue
        seen.add(text)
        options.append(Option(id=text, label=text))
    sj = result.get("suggested_journey")
    if sj in registry and sj not in seen:
        options.append(Option(id=sj, label=f"Guided help: {registry[sj]['title']}"))
    options.append(_HUMAN_CHIP)

    answer = None
    if result.get("kind") == "answer":
        sections: list[AnswerSection] = []
        for s in (result.get("sections") or []):
            items = [str(i) for i in (s.get("items") or []) if str(i).strip()]
            if not items:
                continue
            sections.append(AnswerSection(
                heading=str(s.get("heading") or ""),
                kind=str(s.get("kind") or "list"),
                items=items,
            ))
        uncertainty = result.get("uncertainty") or None
        if sections or uncertainty:
            # short_answer stays empty: the message is shown as the chat bubble, so
            # repeating it here would duplicate it in the answer card.
            answer = StructuredAnswer(
                short_answer="", sections=sections, uncertainty=uncertainty,
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
        privacy_receipt=PrivacyReceipt(
            used_fields=sorted(used), stored_fields=[], storage="local",
            external_llm=settings.llm_external,
        ),
        session=session,
    )


# ── Helpers ─────────────────────────────────────────────────────────────────────


def _is_counselor(label: str) -> bool:
    low = label.lower()
    return "counselor" in low or "counsellor" in low or "human" in low


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


# Full language names the model might return instead of a code (safety net).
_NAME_TO_CODE = {
    "english": "en", "german": "de", "deutsch": "de", "arabic": "ar",
    "persian": "fa", "farsi": "fa", "ukrainian": "uk", "russian": "ru",
    "turkish": "tr", "french": "fr", "spanish": "es", "polish": "pl",
    "italian": "it", "romanian": "ro", "portuguese": "pt",
}


def _detect_language(text: str) -> str:
    """Detect the user's language as an ISO 639-1 code, via the LLM so it works
    for any language (and distinguishes e.g. Farsi vs Arabic, German vs English —
    impossible by script alone). Falls back to a script guess if the LLM is
    unavailable. An explicit slot language overrides this upstream.
    """
    text = (text or "").strip()
    if not text:
        return "en"
    try:
        from core.llm import complete

        out = complete(
            "You are a language detector. Reply with ONLY the ISO 639-1 two-letter "
            "code of the language of the user's message (e.g. en, de, ar, fa, uk, ru, "
            "tr, fr, es, pl). Output the code only — nothing else.",
            text[:400],
        )
        token = "".join(c for c in (out or "").strip().lower() if c.isalpha())
        if len(token) == 2:
            return token
        if token in _NAME_TO_CODE:
            return _NAME_TO_CODE[token]
    except Exception:
        pass
    return _detect_language_by_script(text)


def _detect_language_by_script(text: str) -> str:
    """Offline fallback: Arabic/Persian script -> ar, Cyrillic -> uk, else en."""
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F:
            return "ar"
        if 0x0400 <= o <= 0x04FF:
            return "uk"
    return "en"
