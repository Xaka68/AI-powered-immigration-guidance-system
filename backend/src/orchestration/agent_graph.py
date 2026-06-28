"""LangGraph reasoning agent (single agent, tools, no fixed step cap).

A graph-structured, tool-using agent that UNDERSTANDS before it answers:

    START -> agent(LLM) --tool_calls?--> tools(RAG | web)
               ^------------------- observe --------|
            (no tool_calls / terminal tool) -> END

Tools the agent chooses from:
  - search_official_info : RAG over the indexed Integreat corpus (grounding)
  - search_web           : fallback when the corpus is insufficient (pluggable stub)
  - ask_user             : clarify (options-first) — used until the goal is clear
  - provide_answer       : final grounded answer (structured for our contract)
  - escalate_to_human    : handoff when risky / uncovered

The loop is bounded by ``recursion_limit`` (not a hardcoded number), so it takes
as many steps as it needs. Cross-turn memory is NOT stored server-side: the full
conversation is passed in per call (from the client-side session), which keeps
memory on the device AND isolates conversations (a new chat = empty history).
"""
from __future__ import annotations

import logging
import operator
from functools import lru_cache
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from core.config import settings
from core.types import AnswerSection, Source

log = logging.getLogger(__name__)

_RECURSION_LIMIT = 16  # ~5-6 searches + answer: comprehensive, but trims extra loops


# ── Tool schemas (bind_tools uses the class name as the tool name) ─────────────────


class search_official_info(BaseModel):
    """Search the official Integreat migrant-guidance content. Use this to ground
    any factual answer about procedures, documents, offices, or services."""

    query: str = Field(description="What to look up, in clear keywords.")


class search_web(BaseModel):
    """Search the public web. Use ONLY when the official content does not contain
    enough to answer."""

    query: str = Field(description="What to look up on the web.")


class ask_user(BaseModel):
    """Ask the user EXACTLY ONE short clarifying question (never several at once).
    Use this whenever you need a detail before giving a precise, grounded answer."""

    message: str = Field(description="ONE short question, in the user's language.")
    options: list[str] = Field(
        default_factory=list,
        description="REQUIRED: 2-5 short tappable choices. Bucket into ranges when "
        "the answer is open-ended (e.g. budget '<300 EUR' / '300-500 EUR' / "
        "'>500 EUR'). The user can also type their own answer.",
    )


class provide_answer(BaseModel):
    """Give the final answer. Ground every fact ONLY in tool results — never invent
    steps, documents, deadlines, addresses, links, or fees. Keep `message` to ONE
    short intro sentence; put the actual content in `sections`."""

    message: str = Field(description="ONE short intro sentence — NOT the full answer.")
    sections: list[AnswerSection] = Field(
        default_factory=list,
        description="The answer body as labelled blocks. Emit ONLY the sections that "
        "fit THIS question — a simple or conceptual answer may need NONE (put it all "
        "in `message`); do not force 'next steps' or 'documents' when they don't "
        "apply. Use kind='steps' for an ordered procedure (concrete actions, with "
        "offices+addresses+hours, booking links, fees, deadlines — actual values), "
        "kind='list' for documents or standalone facts, kind='note' for an important "
        "caveat. Give each section a clear heading. Ground every line in tool results.",
    )
    uncertainty: Optional[str] = Field(default=None, description="If partial/unsure.")
    suggested_journey: Optional[str] = Field(
        default=None, description="A curated journey id to offer, if one directly fits."
    )
    follow_ups: list[str] = Field(
        default_factory=list,
        description="ALWAYS provide 2-4 concrete next actions to OFFER the user as "
        "tappable chips, phrased as offers, e.g. 'Help me register my address "
        "(Anmeldung)', 'Help me get health insurance'. They let the user go deeper.",
    )


class escalate_to_human(BaseModel):
    """Hand off to a human counselor when the case is risky/sensitive, or neither
    official content nor the web covers it."""

    reason: str = Field(description="Why a human is needed (short).")


_TOOLS = [search_official_info, search_web, ask_user, provide_answer, escalate_to_human]
_TERMINAL = {"ask_user", "provide_answer", "escalate_to_human"}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    sources: Annotated[list, operator.add]
    result: Optional[dict]


@lru_cache(maxsize=1)
def _model():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or "not-needed",
        temperature=0.2,
    )


def run_agent(
    history: list[dict], city: str | None, language: str, registry: dict[str, dict]
) -> dict:
    """Run one user turn through the agent graph. ``history`` is the full
    conversation ([{role, content}], ending with the user's latest message).
    Returns a dict: {kind: ask|answer|handoff, message, options, sections,
    uncertainty, suggested_journey, sources}."""
    # tool_choice="required" forces the model to emit a structured tool call every
    # step (ask_user / search / provide_answer / escalate) instead of free prose —
    # so options-first questions and grounded answers are guaranteed, not optional.
    model = _model().bind_tools(_TOOLS, tool_choice="required")
    graph = _build_graph(model, city, language)
    init: AgentState = {
        "messages": [SystemMessage(content=_system_prompt(registry, language, city))]
        + _to_messages(history),
        "sources": [],
        "result": None,
    }
    try:
        final = graph.invoke(init, config={"recursion_limit": _RECURSION_LIMIT})
    except Exception as exc:  # noqa: BLE001 — e.g. recursion limit; degrade to handoff
        log.warning("agent graph failed: %s", exc)
        return {"kind": "handoff",
                "message": "Let me connect you with a counselor who can help.",
                "sources": []}

    result = final.get("result")
    if not result:  # model ended with a plain message -> treat as answer
        last = final["messages"][-1] if final["messages"] else None
        text = getattr(last, "content", "") or "Here is what I found."
        result = {"kind": "answer", "message": text}
    result["sources"] = final.get("sources", [])
    return result


def stream_agent(
    history: list[dict], city: str | None, language: str, registry: dict[str, dict]
):
    """Same loop as ``run_agent`` but a generator that yields step events as they
    happen, for the live reasoning UI. Mirrors the graph's agent/tools cycle and
    guards. The LAST event is ``{"type": "final", "result": {...}}`` carrying the
    same dict ``run_agent`` returns.

    Event shapes:
      {"type": "thinking"}
      {"type": "search", "source": "integreat"|"web", "query": str}
      {"type": "search_result", "source": ..., "count": int}
      {"type": "error", "source": ..., "label": "Fehler | Integreat"}
      {"type": "ask"|"answer"|"handoff"}            # terminal kind reached
      {"type": "final", "result": {...}}
    """
    model = _model().bind_tools(_TOOLS, tool_choice="required")
    messages: list = [SystemMessage(content=_system_prompt(registry, language, city))]
    messages += _to_messages(history)
    sources: list[Source] = []
    result: dict | None = None

    try:
        for _ in range(_RECURSION_LIMIT):
            yield {"type": "thinking"}
            ai = model.invoke(messages)
            messages.append(ai)
            calls = getattr(ai, "tool_calls", []) or []
            if not calls:  # plain message -> treat as answer
                result = {"kind": "answer",
                          "message": getattr(ai, "content", "") or "Here is what I found."}
                break

            tool_msgs: list = []
            for call in calls:
                name, args, cid = call["name"], call.get("args", {}), call["id"]
                if name in ("search_official_info", "search_web"):
                    src = "integreat" if name == "search_official_info" else "web"
                    query = args.get("query", "")
                    yield {"type": "search", "source": src, "query": query}
                    hits = _corpus(query, city, language) if src == "integreat" else _web(query)
                    sources += hits
                    if hits:
                        yield {"type": "search_result", "source": src, "count": len(hits)}
                    else:
                        label = "Fehler | Integreat" if src == "integreat" else "No web results"
                        yield {"type": "error", "source": src, "label": label}
                    tool_msgs.append(ToolMessage(content=_fmt(hits), tool_call_id=cid))
                elif name == "ask_user":
                    opts = list(args.get("options") or [])
                    if len(opts) < 2:
                        tool_msgs.append(ToolMessage(
                            content="REJECTED: ask_user needs 2-5 short tappable options "
                            "(bucket into ranges if open-ended). Ask ONE question with options.",
                            tool_call_id=cid))
                    else:
                        result = {"kind": "ask", "message": args.get("message", ""),
                                  "options": opts}
                        tool_msgs.append(ToolMessage(content="(clarifying question sent)",
                                                     tool_call_id=cid))
                elif name == "provide_answer":
                    if not sources:
                        tool_msgs.append(ToolMessage(
                            content="REJECTED: you have not retrieved any sources. You MUST "
                            "call search_official_info first (or search_web). Do not answer "
                            "from general knowledge. If nothing covers it, escalate_to_human.",
                            tool_call_id=cid))
                    else:
                        yield {"type": "reviewing"}
                        result = {"kind": "answer", "message": args.get("message", ""),
                                  "sections": list(args.get("sections") or []),
                                  "uncertainty": args.get("uncertainty"),
                                  "suggested_journey": args.get("suggested_journey"),
                                  "follow_ups": list(args.get("follow_ups") or [])}
                        tool_msgs.append(ToolMessage(content="(answer delivered)",
                                                     tool_call_id=cid))
                elif name == "escalate_to_human":
                    result = {"kind": "handoff", "message": args.get("reason", "")}
                    tool_msgs.append(ToolMessage(content="(handed off)", tool_call_id=cid))

            messages += tool_msgs
            if result:
                break
    except Exception as exc:  # noqa: BLE001 — degrade to handoff, never 500 mid-stream
        log.warning("agent stream failed: %s", exc)
        result = {"kind": "handoff",
                  "message": "Let me connect you with a counselor who can help."}

    if not result:  # recursion exhausted
        result = {"kind": "handoff",
                  "message": "Let me connect you with a counselor who can help."}
    result["sources"] = sources
    yield {"type": result["kind"]}
    yield {"type": "final", "result": result}


def _build_graph(model, city: str | None, language: str):
    def agent_node(state: AgentState) -> dict:
        return {"messages": [model.invoke(state["messages"])]}

    def tools_node(state: AgentState) -> dict:
        last = state["messages"][-1]
        out: list = []
        new_sources: list[Source] = []
        result: dict | None = None
        for call in getattr(last, "tool_calls", []) or []:
            name, args, cid = call["name"], call.get("args", {}), call["id"]
            if name == "search_official_info":
                hits = _corpus(args.get("query", ""), city, language)
                new_sources += hits
                out.append(ToolMessage(content=_fmt(hits), tool_call_id=cid))
            elif name == "search_web":
                hits = _web(args.get("query", ""))
                new_sources += hits
                out.append(ToolMessage(content=_fmt(hits), tool_call_id=cid))
            elif name == "ask_user":
                opts = list(args.get("options") or [])
                if len(opts) < 2:  # enforce options-first, tappable choices
                    out.append(ToolMessage(
                        content="REJECTED: ask_user needs 2-5 short tappable options "
                        "(bucket into ranges if open-ended). Ask ONE question with options.",
                        tool_call_id=cid))
                else:
                    result = {"kind": "ask", "message": args.get("message", ""), "options": opts}
                    out.append(ToolMessage(content="(clarifying question sent)", tool_call_id=cid))
            elif name == "provide_answer":
                # Grounding guard: refuse to answer without sources. Forces a real
                # search (or an honest handoff) instead of a generic answer.
                if not (state.get("sources") or new_sources):
                    out.append(ToolMessage(
                        content="REJECTED: you have not retrieved any sources. You "
                        "MUST call search_official_info first (or search_web if "
                        "official content is missing). Do not answer from general "
                        "knowledge. If nothing covers it, call escalate_to_human.",
                        tool_call_id=cid))
                else:
                    result = {"kind": "answer", "message": args.get("message", ""),
                              "sections": list(args.get("sections") or []),
                              "uncertainty": args.get("uncertainty"),
                              "suggested_journey": args.get("suggested_journey"),
                              "follow_ups": list(args.get("follow_ups") or [])}
                    out.append(ToolMessage(content="(answer delivered)", tool_call_id=cid))
            elif name == "escalate_to_human":
                result = {"kind": "handoff", "message": args.get("reason", "")}
                out.append(ToolMessage(content="(handed off)", tool_call_id=cid))
        return {"messages": out, "sources": new_sources, "result": result}

    def after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    def after_tools(state: AgentState) -> str:
        return END if state.get("result") else "agent"

    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tools_node)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", after_agent, {"tools": "tools", END: END})
    g.add_conditional_edges("tools", after_tools, {"agent": "agent", END: END})
    return g.compile()


# ── Tool implementations ──────────────────────────────────────────────────────────


def _corpus(query: str, city: str | None, language: str) -> list[Source]:
    try:
        from retrieval import search

        return search.search(query, city, language, k=6)
    except Exception as exc:  # noqa: BLE001
        log.warning("corpus search failed: %s", exc)
        return []


def _web(query: str) -> list[Source]:
    try:
        from retrieval import web_search

        return web_search.search(query)
    except Exception as exc:  # noqa: BLE001
        log.warning("web search failed: %s", exc)
        return []


def _fmt(hits: list[Source]) -> str:
    if not hits:
        return "NO RESULTS. Consider search_web, or escalate_to_human if uncovered."
    return "\n\n".join(
        f"[{i + 1}] {s.title} ({s.url})\n{(s.excerpt or '')[:500]}"
        for i, s in enumerate(hits)
    )


# ── Prompt + message conversion ────────────────────────────────────────────────────


def _system_prompt(registry: dict[str, dict], language: str, city: str | None) -> str:
    import json

    curated = json.dumps(
        [{"id": jid, "title": j["title"]} for jid, j in registry.items()], ensure_ascii=False
    )
    city_line = (
        f"The user's city is {city}."
        if city
        else "You do NOT know the user's city yet — ask for it early; guidance is local."
    )
    return (
        "You are a warm, patient guide for MIGRANTS, refugees, and newcomers in "
        "Germany. Assume the user is new to the country and unfamiliar with how "
        "things work — tailor everything to that: official procedures, support "
        "services, language help, and what migrants specifically need. Generic "
        "advice anyone could Google (e.g. 'check listing websites') is NOT "
        "acceptable and does not help these users.\n\n"
        "UNDERSTAND BEFORE YOU ANSWER — like a friendly step-by-step wizard.\n"
        "  • FIRST read the WHOLE conversation and extract everything the user has "
        "ALREADY told you (city, status, visa type, university, semester, family, "
        "goal). NEVER ask again for anything already provided — re-asking is a bug.\n"
        "  • Then ask ONLY for the genuinely MISSING key details needed to answer "
        "precisely (status/visa, city, housing, household — only the ones you don't "
        "already know). If you already have what you need, go straight to searching "
        "and answering — do not pad with extra questions.\n"
        "  • Ask EXACTLY ONE question per turn. Never put several questions in one "
        "message, and never write long paragraphs — keep each message to 1-2 short "
        "lines.\n"
        "  • ALWAYS use ask_user with 2-5 tappable options (bucket open-ended "
        "answers into ranges, e.g. budget '<300 EUR' / '300-500 EUR' / '>500 EUR'). "
        "The user can also type their own answer.\n"
        "  • Establish, one step at a time, the user's CITY/region and their "
        "concrete situation for this goal. For actionable tasks you usually also "
        "need their visa/residence status, whether they already have an apartment, "
        "and their family/timeline — ask these before answering.\n"
        "  • When the user picks a specific task (e.g. taps 'Help me register my "
        "address'), do NOT immediately give generic steps. FIRST ask the 1-2 KEY "
        "prerequisite questions that change the answer (with options), THEN give the "
        "tailored answer. For Anmeldung that's: 'Do you already have an apartment "
        "with a landlord confirmation (Wohnungsgeberbestätigung)?' and the user's "
        "visa/residence status.\n"
        "After EACH reply, ask yourself: 'Do I now have enough to give a SPECIFIC, "
        "useful answer?' If not, ask the next question (one at a time, with options). "
        "Keep it easy — short questions, clear options. A vague or generic answer "
        "means you asked too few questions.\n\n"
        "GROUND EVERYTHING. Never answer from your own general knowledge. ALWAYS call "
        "search_official_info before provide_answer, and base every fact, step, "
        "office, link, and document ONLY on tool results. If official content is "
        "insufficient, call search_web; if it is still insufficient, say honestly "
        "what you could not confirm and use escalate_to_human. Never invent and "
        "never give generic tips.\n\n"
        "FULLY HELP — put yourself in the migrant's shoes; they need to ACT, not get "
        "a summary. For any actionable task, deliver the CONCRETE specifics:\n"
        "  • the exact office name + address (and opening hours if available),\n"
        "  • the ONLINE appointment/booking link,\n"
        "  • the full document checklist,\n"
        "  • the fee/cost and the deadline,\n"
        "  • what to expect at the appointment.\n"
        "Do NOT say 'look it up online' — look it up FOR them. The Integreat corpus "
        "has the general procedure; for CITY-SPECIFIC operational details it may "
        "lack (the city's booking portal link, office addresses, fees, hours), use "
        "search_web.\n"
        "BE COMPREHENSIVE — a thin answer is a failure. Gather and include the FULL "
        "picture with several focused searches (typically 2-5): e.g. one for the "
        "procedure, one for the city's office(s) + addresses + opening hours, one "
        "for the online booking link, one for the fee. List ALL relevant offices in "
        "the city (not just one), each with address + hours, the full document "
        "checklist, the fee, the deadline, and contact info. Then answer.\n"
        "FINDINGS-DRIVEN CLARIFICATION: if a search reveals the answer BRANCHES on "
        "something you do not yet know (e.g. main vs secondary residence, the user's "
        "district, with/without children, a specific visa type), ask the user that "
        "question (ask_user, with options taken from what you found) BEFORE "
        "answering — even mid-research. Don't guess the branch.\n\n"
        "BE PROACTIVE. Every answer MUST include follow_ups: 2-4 next actions as "
        "chips that are DYNAMIC and specific to THIS answer and what you found — not "
        "a fixed list. Derive them from the findings, e.g. if you found several "
        "offices: 'Find my nearest office'; if booking is online: 'Help me book an "
        "appointment'; or 'What if I don't have a landlord confirmation?'. Do NOT "
        "include a counselor option (it is added automatically).\n\n"
        "Tools: ask_user (clarify, options-first) · search_official_info (RAG) · "
        "search_web (city-specific details + fallback) · provide_answer (grounded, "
        "structured) · escalate_to_human. Set suggested_journey to a curated journey "
        "id if one directly fits.\n"
        "Be warm and friendly — use the occasional tasteful emoji (👋 ✅ 📋 🏠 🗓️), "
        "not in every line.\n"
        f"Write ALL user-facing text in the user's language ({language}). {city_line}\n"
        f"Curated journeys you may suggest: {curated}"
    )


def _to_messages(history: list[dict]):
    out = []
    for h in history:
        role, content = h.get("role"), h.get("content", "")
        if role == "assistant":
            out.append(AIMessage(content=content))
        else:
            out.append(HumanMessage(content=content))
    return out
