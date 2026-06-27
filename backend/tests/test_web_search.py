"""Web-search tool: result mapping + graceful failure (no real network)."""
import ddgs

from core.types import Source
from retrieval import web_search


def test_maps_results_to_sources(monkeypatch):
    class FakeDDGS:
        def text(self, query, max_results=5):
            return [
                {"title": "Residence Registration", "href": "https://x/anmeldung",
                 "body": "Register your address at the Bürgerbüro."},
                {"title": "No URL", "body": "skipped"},  # dropped (no url)
            ]

    monkeypatch.setattr(ddgs, "DDGS", FakeDDGS)
    out = web_search.search("anmeldung munich", k=5)
    assert len(out) == 1
    assert isinstance(out[0], Source)
    assert out[0].url == "https://x/anmeldung"
    assert "Register" in out[0].excerpt
    assert out[0].last_updated is None


def test_returns_empty_on_failure(monkeypatch):
    class Boom:
        def text(self, *a, **k):
            raise RuntimeError("network down")

    monkeypatch.setattr(ddgs, "DDGS", Boom)
    assert web_search.search("anything") == []
