"""A2 — graph engine: deterministic transitions + escalation for the demo graph."""
from orchestration import graph_engine as ge


def test_first_stage(registry):
    j = registry["address_registration"]
    assert ge.first_stage_id(j) == "housing_status"


def test_missing_slots(registry):
    j = registry["address_registration"]
    stage = ge.get_stage(j, "housing_status")
    assert ge.missing_slots(stage, {}) == ["housing_status"]
    assert ge.missing_slots(stage, {"housing_status": "has_apartment"}) == []


def test_transition_has_apartment_goes_to_documents(registry):
    j = registry["address_registration"]
    assert ge.next_stage(j, "housing_status", {"housing_status": "has_apartment"}) == "documents"


def test_transition_looking_routes_out(registry):
    j = registry["address_registration"]
    assert ge.next_stage(j, "housing_status", {"housing_status": "looking"}) == "ROUTE:housing_search"


def test_no_rule_match_returns_none(registry):
    j = registry["address_registration"]
    assert ge.next_stage(j, "housing_status", {"housing_status": "??"}) is None


def test_escalation_on_high_urgency(registry):
    j = registry["address_registration"]
    stage = ge.get_stage(j, "housing_status")
    assert ge.check_escalation(stage, {"urgency": "high"}) == "HANDOFF"
    assert ge.check_escalation(stage, {"urgency": "normal"}) is None


def test_content_stage_detection(registry):
    j = registry["address_registration"]
    assert ge.is_content_stage(ge.get_stage(j, "documents")) is True
    assert ge.is_content_stage(ge.get_stage(j, "housing_status")) is False
