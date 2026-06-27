"""A4 — router: gated, multi-intent (offline keyword fallback path)."""
from orchestration.router import classify


def test_multi_intent_kita_and_deutschkurs(registry):
    out = classify("I need Kita and Deutschkurs", registry)
    assert set(out["journey_ids"]) == {"school_childcare", "german_course"}


def test_single_intent_registration(registry):
    out = classify("I found an apartment and need Anmeldung", registry)
    assert out["journey_ids"][0] == "address_registration"


def test_router_is_gated_to_known_journeys(registry):
    out = classify("I want to climb Mount Everest", registry)
    # No known journey matches -> empty, never an invented id.
    assert out["journey_ids"] == []


def test_extracts_city_and_urgency(registry):
    out = classify("I am in Munich and it is urgent", registry)
    assert out["extracted_slots"].get("city") == "Munich"
    assert out["extracted_slots"].get("urgency") == "high"
