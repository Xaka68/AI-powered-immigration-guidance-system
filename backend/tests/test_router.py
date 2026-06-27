"""A4 — router: LLM classification (gated) + embedding fallback.

Both paths are stubbed for determinism — we test the router's own logic (gating,
multi-intent, slot passthrough, semantic fallback), not the model or the network.
"""
import core.llm
import orchestration.router as router_mod
from orchestration.router import classify


class _KeySettings:
    llm_api_key = "test-key"  # forces the LLM path


class _NoKeySettings:
    llm_api_key = ""  # forces the embedding fallback


def _stub_llm(monkeypatch, payload):
    monkeypatch.setattr(router_mod, "settings", _KeySettings())
    monkeypatch.setattr(core.llm, "complete", lambda system, user, **kw: payload)


# --- LLM path --------------------------------------------------------------------


def test_gated_to_known_journeys(registry, monkeypatch):
    # Model returns an invented id alongside a real one -> invented id filtered out.
    _stub_llm(monkeypatch, {"journey_ids": ["everest_expedition", "address_registration"],
                            "extracted_slots": {}})
    out = classify("anything", registry)
    assert out["journey_ids"] == ["address_registration"]


def test_multi_intent_preserved(registry, monkeypatch):
    _stub_llm(monkeypatch, {"journey_ids": ["school_childcare", "german_course"],
                            "extracted_slots": {}})
    out = classify("I need Kita and Deutschkurs", registry)
    assert set(out["journey_ids"]) == {"school_childcare", "german_course"}


def test_slots_passed_through(registry, monkeypatch):
    _stub_llm(monkeypatch, {"journey_ids": ["address_registration"],
                            "extracted_slots": {"city": "Munich", "urgency": "high",
                                                "language": "ar", "blank": ""}})
    out = classify("I am in Munich and it is urgent", registry)
    assert out["extracted_slots"]["city"] == "Munich"
    assert out["extracted_slots"]["urgency"] == "high"
    assert "blank" not in out["extracted_slots"]  # falsy slots dropped


def test_empty_message_returns_nothing(registry):
    assert classify("   ", registry)["journey_ids"] == []


# --- Embedding fallback (no LLM key) ---------------------------------------------


def test_embedding_fallback_picks_best(registry, monkeypatch):
    monkeypatch.setattr(router_mod, "settings", _NoKeySettings())
    ids = list(registry)
    # Journey 0 is colinear with the query vector; the rest are orthogonal.
    monkeypatch.setattr(router_mod, "_journey_embeddings",
                        lambda j: (ids, [[1.0, 0.0] if i == 0 else [0.0, 1.0]
                                         for i in range(len(ids))]))
    monkeypatch.setattr("retrieval.embeddings.embed_queries", lambda texts: [[1.0, 0.0]])
    out = classify("some message", registry)
    assert out["journey_ids"] == [ids[0]]


def test_embedding_fallback_gates_offtopic(registry, monkeypatch):
    monkeypatch.setattr(router_mod, "settings", _NoKeySettings())
    ids = list(registry)
    # All journeys near-orthogonal to the query -> below _MIN_SIM -> no match.
    monkeypatch.setattr(router_mod, "_journey_embeddings",
                        lambda j: (ids, [[0.0, 1.0] for _ in ids]))
    monkeypatch.setattr("retrieval.embeddings.embed_queries", lambda texts: [[1.0, 0.0]])
    out = classify("climb mount everest", registry)
    assert out["journey_ids"] == []
