"""A6 pipeline end-to-end (with A3 slots, A5 chips, A7 handoff).

Retrieval (Track B) is faked so the orchestration loop can be tested in isolation.
"""
import pytest

from core.types import ChatRequest, Session, Source, StructuredAnswer
from orchestration.pipeline import run_turn


@pytest.fixture
def fake_retrieval(monkeypatch):
    """Patch the retrieval seam with deterministic fakes."""
    import retrieval.answer_generator as ag
    import retrieval.faithfulness_check as fc
    import retrieval.search as se

    sources = [
        Source(
            title="Anmeldung — registering your address",
            url="https://example.org/anmeldung",
            last_updated="2025-03-01",
            language="de",
            excerpt="Register within two weeks of moving in.",
        )
    ]
    monkeypatch.setattr(se, "search", lambda q, city, language, k=5: sources)
    monkeypatch.setattr(
        ag,
        "generate_answer",
        lambda goal, lang, srcs, slots: StructuredAnswer(
            short_answer="Register your address at the Bürgerbüro.",
            next_steps=["Get landlord confirmation", "Book an appointment"],
            documents_needed=["Passport", "Landlord confirmation"],
        ),
    )
    monkeypatch.setattr(fc, "check", lambda answer, srcs: answer)
    return sources


def test_cold_start_offers_journey_chips(registry):
    resp = run_turn(ChatRequest(), registry)
    assert resp.journey_id is None
    ids = {o.id for o in resp.options}
    assert {"address_registration", "german_course"} <= ids
    assert "talk_to_human" in ids


def test_select_journey_then_asks_slot_with_chips(registry):
    resp = run_turn(ChatRequest(option_id="address_registration"), registry)
    assert resp.journey_id == "address_registration"
    assert resp.stage_id == "housing_status"
    labels = {o.id for o in resp.options}
    assert {"has_apartment", "looking", "temporary", "talk_to_human"} <= labels
    assert resp.answer is None  # still clarifying, no content yet


def test_full_address_registration_to_grounded_answer(registry, fake_retrieval):
    r1 = run_turn(ChatRequest(option_id="address_registration"), registry)
    r2 = run_turn(ChatRequest(option_id="has_apartment", session=r1.session), registry)
    assert r2.stage_id == "documents"
    assert r2.answer is not None
    assert r2.answer.next_steps
    assert len(r2.sources) == 1 and r2.sources[0].last_updated == "2025-03-01"
    # edge-case chips + human handoff surface as next options
    option_ids = {o.id for o in r2.options}
    assert "missing_landlord_confirmation" in option_ids
    assert "talk_to_human" in option_ids
    # privacy receipt reflects only used slots, stored locally
    assert r2.privacy_receipt.storage == "local"
    assert r2.privacy_receipt.stored_fields == []


def test_content_stage_degrades_gracefully_without_retrieval(registry, monkeypatch):
    """If retrieval is unavailable (any error), a content stage must not crash —
    it returns a safe answer, no sources, an uncertainty note, and a human exit.
    (Track B is now wired, so we force a failure to test the fallback offline.)"""
    import retrieval.search as se

    def _boom(*args, **kwargs):
        raise RuntimeError("index unavailable")

    monkeypatch.setattr(se, "search", _boom)
    r1 = run_turn(ChatRequest(option_id="address_registration"), registry)
    r2 = run_turn(ChatRequest(option_id="has_apartment", session=r1.session), registry)
    assert r2.answer is not None
    assert r2.sources == []
    assert r2.answer.uncertainty  # flags that info could not be verified
    assert "talk_to_human" in {o.id for o in r2.options}


def _no_curated_match(monkeypatch):
    """Force the router to find no curated journey -> the dynamic path."""
    import orchestration.router as router

    monkeypatch.setattr(router, "classify", lambda m, reg: {"journey_ids": [], "extracted_slots": {}})


def test_agent_clarify_then_answer_with_memory(registry, monkeypatch):
    """The agent asks first (options-first), then answers grounded on the next
    turn; the conversation history is kept across turns (context)."""
    import orchestration.agent_graph as agent_graph

    _no_curated_match(monkeypatch)
    calls = {"n": 0}

    def fake_run_agent(history, city, language, registry):
        calls["n"] += 1
        if calls["n"] == 1:  # turn 1: clarify, options-first
            return {"kind": "ask", "message": "University-level or vocational?",
                    "options": ["University-level", "Vocational"], "sources": []}
        return {"kind": "answer", "message": "Contact the recognition office.",
                "next_steps": ["Contact the office"], "documents_needed": ["Diploma"],
                "sources": [Source(title="Recognition", url="https://x/anerkennung",
                                   last_updated="2025-01-01", language="en", excerpt="...")]}

    monkeypatch.setattr(agent_graph, "run_agent", fake_run_agent)

    r1 = run_turn(ChatRequest(message="can I work as a nurse with my Syrian diploma?"), registry)
    assert r1.journey_id is None and r1.session.dynamic is not None
    assert r1.answer is None  # a question, not an answer, first turn
    assert {"University-level", "Vocational", "talk_to_human"} <= {o.id for o in r1.options}
    assert r1.session.dynamic.history[-1]["role"] == "assistant"  # memory kept

    r2 = run_turn(ChatRequest(option_id="University-level", session=r1.session), registry)
    assert r2.answer is not None and r2.answer.next_steps  # grounded answer
    assert len(r2.sources) == 1
    # the tapped choice was recorded into the conversation history
    assert any(h["content"] == "University-level" for h in r2.session.dynamic.history)


def test_agent_memory_isolation_between_conversations(registry, monkeypatch):
    """A fresh session must NOT see a previous conversation's history (no bleed)."""
    import orchestration.agent_graph as agent_graph

    _no_curated_match(monkeypatch)
    seen: list[list[str]] = []

    def fake_run_agent(history, city, language, registry):
        seen.append([h["content"] for h in history])
        return {"kind": "answer", "message": "ok", "sources": []}

    monkeypatch.setattr(agent_graph, "run_agent", fake_run_agent)

    run_turn(ChatRequest(message="question A"), registry)  # conversation A
    run_turn(ChatRequest(message="question B"), registry)  # NEW conversation (fresh session)
    assert seen[0] == ["question A"]
    assert seen[1] == ["question B"]  # A did not leak into B


def test_agent_suggests_curated_journey(registry, monkeypatch):
    """The agent can suggest a curated journey; tapping it enters the gold path."""
    import orchestration.agent_graph as agent_graph

    _no_curated_match(monkeypatch)
    monkeypatch.setattr(agent_graph, "run_agent", lambda history, city, language, registry: {
        "kind": "ask", "message": "Sounds like you need to register your address.",
        "options": [], "suggested_journey": "address_registration", "sources": []})

    r1 = run_turn(ChatRequest(message="I moved into a flat, what official stuff do I do"), registry)
    assert "address_registration" in {o.id for o in r1.options}  # suggested curated chip
    r2 = run_turn(ChatRequest(option_id="address_registration", session=r1.session), registry)
    assert r2.journey_id == "address_registration"  # entered the curated journey
    assert r2.session.dynamic is None  # dynamic state cleared


def test_agent_failure_degrades_to_handoff(registry, monkeypatch):
    """If the agent raises, the turn must not 500 — it routes to a human."""
    import orchestration.agent_graph as agent_graph

    _no_curated_match(monkeypatch)

    def boom(*a, **k):
        raise RuntimeError("agent down")

    monkeypatch.setattr(agent_graph, "run_agent", boom)
    r = run_turn(ChatRequest(message="some open ended question"), registry)
    assert r.requires_handoff is True and r.handoff_summary is not None
    assert "talk_to_human" in {o.id for o in r.options}


def test_agent_graph_tool_loop_with_fake_model(monkeypatch):
    """The LangGraph loop runs tools then answers, capturing sources — verified
    with a fake model (no real LLM call)."""
    import orchestration.agent_graph as agent_graph
    import retrieval.search as se
    from langchain_core.messages import AIMessage

    monkeypatch.setattr(se, "search", lambda q, city, language, k=6: [
        Source(title="Anmeldung", url="https://x/anmeldung", last_updated="2025-03-01",
               language="de", excerpt="Register your address."),
    ])

    class _FakeModel:
        def __init__(self):
            self.n = 0

        def bind_tools(self, tools):
            return self

        def invoke(self, messages):
            self.n += 1
            if self.n == 1:  # first: call the RAG tool
                return AIMessage(content="", tool_calls=[
                    {"name": "search_official_info", "args": {"query": "anmeldung"},
                     "id": "c1", "type": "tool_call"}])
            return AIMessage(content="", tool_calls=[  # then: deliver the answer
                {"name": "provide_answer",
                 "args": {"message": "Register at the Bürgerbüro.", "next_steps": ["Book appt"]},
                 "id": "c2", "type": "tool_call"}])

    monkeypatch.setattr(agent_graph, "_model", lambda: _FakeModel())

    result = agent_graph.run_agent(
        history=[{"role": "user", "content": "how do I register my address?"}],
        city="Munich", language="en", registry={})
    assert result["kind"] == "answer"
    assert result["next_steps"] == ["Book appt"]
    assert any(s.url == "https://x/anmeldung" for s in result["sources"])  # tool source captured


def test_multi_intent_asks_which_first(registry):
    resp = run_turn(ChatRequest(message="I need Kita and Deutschkurs"), registry)
    assert resp.journey_id is None  # not committed yet
    ids = {o.id for o in resp.options}
    assert {"school_childcare", "german_course"} <= ids


def test_high_urgency_escalates_to_handoff(registry):
    session = Session(
        journey_id="address_registration",
        stage_id="housing_status",
        slots={"urgency": "high"},
    )
    resp = run_turn(ChatRequest(session=session), registry)
    assert resp.requires_handoff is True
    assert resp.handoff_summary is not None
    assert resp.handoff_summary.urgency == "high"


def test_explicit_human_request_handoff(registry):
    session = Session(journey_id="address_registration", stage_id="documents")
    resp = run_turn(ChatRequest(option_id="talk_to_human", session=session), registry)
    assert resp.requires_handoff is True
    assert resp.handoff_summary is not None
    assert "Anmeldung" in resp.handoff_summary.user_goal or resp.handoff_summary.user_goal


def test_looking_routes_into_housing_search(registry, fake_retrieval):
    r1 = run_turn(ChatRequest(option_id="address_registration"), registry)
    r2 = run_turn(ChatRequest(option_id="looking", session=r1.session), registry)
    # ROUTE:housing_search -> lands in the housing_search journey's content stage
    assert r2.journey_id == "housing_search"
    assert r2.answer is not None
