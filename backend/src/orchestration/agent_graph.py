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
from core.types import Source

log = logging.getLogger(__name__)

_RECURSION_LIMIT = 14  # ~6 tool calls per turn: enough to gather specifics, bounded


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
    short intro sentence; put the actual content in next_steps + documents_needed."""

    message: str = Field(description="ONE short intro sentence — NOT the full answer.")
    next_steps: list[str] = Field(
        default_factory=list,
        description="Concrete, ordered actions. Include the ACTUAL address, booking "
        "link, fee, and deadline in the step text — not 'look it up online'.",
    )
    documents_needed: list[str] = Field(default_factory=list)
    uncertainty: Optional[str] = Field(default=None, description="If partial/unsure.")
    suggested_journey: Optional[str] = Field(
        default=None, description="A curated journey id to offer, if one directly fits."
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
    Returns a dict: {kind: ask|answer|handoff, message, options, next_steps,
    documents_needed, uncertainty, suggested_journey, sources}."""
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
    final = graph.invoke(init, config={"recursion_limit": _RECURSION_LIMIT})

    result = final.get("result")
    if not result:  # model ended with a plain message -> treat as answer
        last = final["messages"][-1] if final["messages"] else None
        text = getattr(last, "content", "") or "Here is what I found."
        result = {"kind": "answer", "message": text}
    result["sources"] = final.get("sources", [])
    return result


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
                              "next_steps": list(args.get("next_steps") or []),
                              "documents_needed": list(args.get("documents_needed") or []),
                              "uncertainty": args.get("uncertainty"),
                              "suggested_journey": args.get("suggested_journey")}
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
        "UNDERSTAND BEFORE YOU ANSWER — like a friendly step-by-step wizard:\n"
        "  • Ask EXACTLY ONE question per turn. Never put several questions in one "
        "message, and never write long paragraphs — keep each message to 1-2 short "
        "lines.\n"
        "  • ALWAYS use ask_user with 2-5 tappable options (bucket open-ended "
        "answers into ranges, e.g. budget '<300 EUR' / '300-500 EUR' / '>500 EUR'). "
        "The user can also type their own answer.\n"
        "  • Establish, one step at a time, at least the user's CITY/region and "
        "their concrete situation for this goal (status, budget, timeline, what "
        "they've tried) before answering.\n"
        "A vague or generic answer means you asked too few questions — ask more, one "
        "at a time with options, instead.\n\n"
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
        "search_web. Run a FEW focused searches (typically 1-3 total) to gather the "
        "key specifics, then answer — do not loop endlessly. If after that the user "
        "still lacks enough to act, ask the next needed question instead.\n\n"
        "Tools: ask_user (clarify, options-first) · search_official_info (RAG) · "
        "search_web (city-specific details + fallback) · provide_answer (grounded, "
        "structured) · escalate_to_human. Set suggested_journey to a curated journey "
        "id if one directly fits.\n"
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
