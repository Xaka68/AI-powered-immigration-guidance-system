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


def test_tier2_oneshot_qa_when_no_journey_fits(registry, monkeypatch):
    """A free-text question with no matching journey gets a grounded answer from
    the corpus (Tier 2), not a dead-end — with sources, journey_id None, human exit."""
    import retrieval.answer_generator as ag
    import retrieval.faithfulness_check as fc
    import retrieval.search as se

    srcs = [Source(title="Free legal advice — counseling offices", url="https://x/legal",
                   last_updated="2025-02-01", language="en", excerpt="Where to get free advice.")]
    monkeypatch.setattr(se, "search", lambda q, city, language, k=5: srcs)
    monkeypatch.setattr(ag, "generate_answer",
                        lambda goal, lang, s, slots: StructuredAnswer(
                            short_answer="You can get free legal advice at a counseling office."))
    monkeypatch.setattr(fc, "check", lambda a, s: a)

    resp = run_turn(ChatRequest(message="where can I get free legal advice?"), registry)
    assert resp.journey_id is None          # one-shot, not a journey
    assert resp.answer is not None
    assert len(resp.sources) == 1
    assert "talk_to_human" in {o.id for o in resp.options}


def test_tier2_no_sources_offers_journeys_not_fabrication(registry, monkeypatch):
    """If the corpus has nothing, Tier 2 must not invent — fall back to guidance."""
    import retrieval.search as se

    monkeypatch.setattr(se, "search", lambda q, city, language, k=5: [])
    resp = run_turn(ChatRequest(message="totally unrelated zzzqqq question"), registry)
    assert resp.answer is None
    assert {"talk_to_human"} <= {o.id for o in resp.options}


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
