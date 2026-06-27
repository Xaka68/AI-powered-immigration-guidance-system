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
        lambda goal, lang, srcs, slots, history=None: StructuredAnswer(
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
    assert r2.sources[0].excerpt == ""  # excerpts stripped before reaching the client (FR-005)
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


def test_free_text_gets_clarifying_question(registry, monkeypatch):
    """Vague free text -> context_engine asks a clarifying question, no journey chips."""
    import orchestration.context_engine as ce

    monkeypatch.setattr(
        ce,
        "run_turn",
        lambda msg, hist, facts, reg: {
            "action": "ask",
            "question": "What city are you living in?",
            "options": ["Munich", "Berlin", "Hamburg"],
        },
    )
    r = run_turn(ChatRequest(message="I need help"), registry)
    assert r.journey_id is None
    assert r.assistant_message == "What city are you living in?"
    assert r.options == []  # context_engine options not surfaced as chips yet
    assert r.answer is None


def test_free_text_with_context_gets_grounded_answer(registry, monkeypatch, fake_retrieval):
    """When context_engine knows enough, pipeline calls RAG and returns a grounded answer."""
    import orchestration.context_engine as ce

    monkeypatch.setattr(
        ce,
        "run_turn",
        lambda msg, hist, facts, reg: {
            "action": "answer",
            "query_for_rag": "Anmeldung address registration Munich",
            "facts_extracted": {"city": "Munich", "language": "en"},
        },
    )
    r = run_turn(ChatRequest(message="how do I register my address in Munich?"), registry)
    assert r.answer is not None
    assert r.answer.next_steps
    assert len(r.sources) == 1
    assert r.session.slots.get("city") == "Munich"


def test_free_text_no_rag_results_acknowledges_uncertainty(registry, monkeypatch):
    """When context_engine says answer but RAG returns nothing, acknowledge uncertainty."""
    import orchestration.context_engine as ce
    import retrieval.search as se

    monkeypatch.setattr(
        ce,
        "run_turn",
        lambda msg, hist, facts, reg: {
            "action": "answer",
            "query_for_rag": "very obscure topic",
            "facts_extracted": {},
        },
    )
    monkeypatch.setattr(se, "search", lambda q, city, language, k=5: [])

    r = run_turn(ChatRequest(message="some very obscure question"), registry)
    assert r.answer is None  # no grounded answer
    assert "counselor" in r.assistant_message.lower() or "human" in r.assistant_message.lower()
    assert any(o.id == "talk_to_human" for o in r.options)


def test_free_text_engine_failure_degrades_to_handoff(registry, monkeypatch):
    """If context_engine raises, the pipeline falls back to a human handoff."""
    import orchestration.context_engine as ce

    def boom(*a, **k):
        raise RuntimeError("engine down")

    monkeypatch.setattr(ce, "run_turn", boom)
    r = run_turn(ChatRequest(message="some open ended question"), registry)
    assert r.requires_handoff is True and r.handoff_summary is not None


def test_multi_intent_free_text_gets_clarifying_question(registry, monkeypatch):
    """Multi-intent free text goes through context_engine — no raw journey chips."""
    import orchestration.context_engine as ce

    monkeypatch.setattr(
        ce,
        "run_turn",
        lambda msg, hist, facts, reg: {
            "action": "ask",
            "question": "Which would you like to start with — childcare or a German course?",
            "options": ["Childcare (Kita)", "German course"],
        },
    )
    r = run_turn(ChatRequest(message="I need Kita and Deutschkurs"), registry)
    assert r.journey_id is None
    assert "childcare" in r.assistant_message.lower() or "kita" in r.assistant_message.lower()
    assert r.options == []  # routing is invisible — no raw journey chips


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
