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


def test_cold_start_returns_no_chips(registry):
    # Welcome screen is client-side; cold-start API call returns no options.
    resp = run_turn(ChatRequest(), registry)
    assert resp.journey_id is None
    assert resp.options == []


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


def test_agent_clarifies_then_retrieves_then_answers(registry, monkeypatch):
    """The agent asks first (options-first), then on the next turn retrieves and
    answers grounded — and remembers the answer to its question (context)."""
    import core.llm as llm
    import retrieval.search as se

    _no_curated_match(monkeypatch)
    monkeypatch.setattr(se, "search", lambda q, city, language, k=6: [
        Source(title="Recognition of foreign professional qualifications",
               url="https://x/anerkennung", last_updated="2025-01-01",
               language="en", excerpt="How recognition works for nurses."),
    ])
    roadmap = ["Identify your qualification", "Find the recognition office", "Submit documents"]
    calls = {"n": 0}

    def fake_complete(system, user, json_schema=None, temperature=0.2):
        calls["n"] += 1
        if calls["n"] == 1:  # turn 1: ask (understand first)
            return {"action": "ask", "roadmap": roadmap, "current_step_index": 0,
                    "assistant_message": "Is your nursing qualification university-level or vocational?",
                    "ask_slot": "qualification_level",
                    "options": [{"id": "university", "label": "University-level"},
                                {"id": "vocational", "label": "Vocational"}]}
        if calls["n"] == 2:  # turn 2, step 1: retrieve
            return {"action": "retrieve", "query": "nurse qualification recognition Germany"}
        return {"action": "answer", "current_step_index": 1,  # turn 2, step 2: grounded answer
                "assistant_message": "Contact the recognition office for nurses.",
                "next_steps": ["Contact the recognition office", "Prepare your diploma"],
                "documents_needed": ["Diploma", "Passport"]}

    monkeypatch.setattr(llm, "complete", fake_complete)

    r1 = run_turn(ChatRequest(message="can I work as a nurse with my Syrian diploma?"), registry)
    assert r1.journey_id is None and r1.session.dynamic is not None
    assert r1.roadmap == roadmap and r1.roadmap_step == 0
    assert {"university", "vocational", "talk_to_human"} <= {o.id for o in r1.options}
    assert r1.answer is None  # a question, not an answer, on the first turn
    assert r1.session.dynamic.history[-1]["role"] == "assistant"  # memory kept

    r2 = run_turn(ChatRequest(option_id="university", session=r1.session), registry)
    assert r2.session.dynamic.facts.get("qualification_level") == "university"  # remembered
    assert r2.roadmap_step == 1
    assert r2.answer is not None and r2.answer.next_steps  # grounded step
    assert len(r2.sources) == 1


def test_agent_falls_back_to_web_when_corpus_empty(registry, monkeypatch):
    """Corpus has nothing -> agent uses the web-search tool -> answers from it."""
    import core.llm as llm
    import retrieval.search as se
    import retrieval.web_search as ws

    _no_curated_match(monkeypatch)
    monkeypatch.setattr(se, "search", lambda q, city, language, k=6: [])  # corpus empty
    monkeypatch.setattr(ws, "search", lambda q, k=5: [
        Source(title="Web result", url="https://web/x", last_updated=None,
               language="en", excerpt="Found on the web."),
    ])
    calls = {"n": 0}

    def fake_complete(system, user, json_schema=None, temperature=0.2):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"action": "retrieve", "query": "obscure question"}
        if calls["n"] == 2:
            return {"action": "web_search", "query": "obscure question"}
        return {"action": "answer", "assistant_message": "Here's what the web says.",
                "next_steps": ["Do the thing"]}

    monkeypatch.setattr(llm, "complete", fake_complete)
    r = run_turn(ChatRequest(message="some very obscure question"), registry)
    assert r.answer is not None
    assert any(s.url == "https://web/x" for s in r.sources)  # web result cited


def test_dynamic_can_route_into_curated_journey(registry, monkeypatch):
    """The agent can suggest a curated journey; tapping it enters the gold path."""
    import core.llm as llm
    import retrieval.search as se

    _no_curated_match(monkeypatch)
    monkeypatch.setattr(se, "search", lambda q, city, language, k=6: [])
    monkeypatch.setattr(llm, "complete", lambda system, user, json_schema=None, temperature=0.2: {
        "action": "ask",
        "assistant_message": "Sounds like you need to register your address — I can guide you.",
        "ask_slot": "confirm", "options": [],
        "suggested_journey_id": "address_registration"})

    r1 = run_turn(ChatRequest(message="I moved into a flat, what official stuff do I do"), registry)
    assert "address_registration" in {o.id for o in r1.options}  # suggested curated chip
    r2 = run_turn(ChatRequest(option_id="address_registration", session=r1.session), registry)
    assert r2.journey_id == "address_registration"  # entered the curated journey
    assert r2.session.dynamic is None  # dynamic state cleared


def test_dynamic_planner_failure_degrades_to_handoff(registry, monkeypatch):
    """If the planner LLM fails, the turn must not 500 — it routes to a human."""
    import core.llm as llm
    import retrieval.search as se

    _no_curated_match(monkeypatch)
    monkeypatch.setattr(se, "search", lambda q, city, language, k=6: [])

    def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr(llm, "complete", boom)
    r = run_turn(ChatRequest(message="some open ended question"), registry)
    assert r.requires_handoff is True and r.handoff_summary is not None
    assert "talk_to_human" in {o.id for o in r.options}


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
