"""A1 — loader: dir-scan, validation, and the ignore rules."""
from tests.conftest import FIXTURES

from orchestration.loader import load_journeys


def test_loads_known_journeys():
    reg = load_journeys(FIXTURES)
    assert "address_registration" in reg
    assert reg["address_registration"]["title"].startswith("Register")


def test_ignores_underscore_and_schema_files():
    reg = load_journeys(FIXTURES)
    # _ignored.json must not appear under any id.
    assert "should_not_load" not in reg
    assert "schema" not in reg


def test_registry_keyed_by_id():
    reg = load_journeys(FIXTURES)
    for jid, journey in reg.items():
        assert jid == journey["id"]
