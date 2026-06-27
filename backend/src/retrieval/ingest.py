"""Track B (Daril) — Ingest Integreat pages into data/sources/pages.json.

Fetches every page for the configured region (``settings.integreat_region``) in
each requested language from the Integreat WP-JSON API, normalizes it, and writes
a flat JSON list. No city is hardcoded. Public API (seam, PROTOCOL.md §4.3):

    fetch_pages(languages=None) -> list[dict]
    run() -> None      # writes data/sources/pages.json

CLI:  python -m retrieval.ingest      (with backend/src on PYTHONPATH)
"""
from __future__ import annotations

import json
import os
import re

import httpx

from core.config import settings

API_TEMPLATE = "https://cms.integreat-app.de/{region}/{lang}/wp-json/extensions/v3/pages/"

# Default languages: de is the grounding corpus; the rest enable multilingual
# retrieval + cross-language linking (incl. non-Latin ar/uk/fa). Override via env.
DEFAULT_LANGUAGES = os.getenv("INGEST_LANGUAGES", "de,en,ar,uk,fa").split(",")

# The CMS serves the admin host; rewrite to the public app domain so cited URLs
# are user-openable.
_ADMIN_HOST = "admin.integreat-app.de"
_PUBLIC_HOST = "integreat.app"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t ]+")
_NL_RE = re.compile(r"\n{3,}")


def html_to_text(html: str) -> str:
    """Strip HTML to readable plain text (BeautifulSoup if available, else regex)."""
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for block in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "div", "tr"]):
            block.append("\n")
        text = soup.get_text()
    except Exception:
        text = _TAG_RE.sub(" ", html)
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _public_url(url: str | None) -> str | None:
    return url.replace(_ADMIN_HOST, _PUBLIC_HOST) if url else url


def normalize(page: dict, language: str) -> dict:
    """Map one raw API page to our stored schema (PROTOCOL.md Track B-B1)."""
    available = page.get("available_languages") or {}
    parent = page.get("parent") or {}
    return {
        "id": page.get("id"),
        "title": (page.get("title") or "").strip(),
        "url": _public_url(page.get("url")),
        "content": html_to_text(page.get("content") or ""),
        "excerpt": (page.get("excerpt") or "").strip(),
        "last_updated": page.get("last_updated") or page.get("modified_gmt"),
        "language": language,
        "parent_id": (parent.get("id") or None),
        # cross-language links {lang: page_id} so retrieval can hop de<->ar etc.
        "available_languages": {
            lang: info.get("id") for lang, info in available.items() if info
        },
    }


def fetch_pages(languages: list[str] | None = None) -> list[dict]:
    """Fetch + normalize all pages for the configured region across `languages`."""
    languages = languages or DEFAULT_LANGUAGES
    region = settings.integreat_region
    pages: list[dict] = []
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        for lang in (lang.strip() for lang in languages):
            try:
                resp = client.get(API_TEMPLATE.format(region=region, lang=lang))
                resp.raise_for_status()
                batch = [normalize(p, lang) for p in resp.json()]
                pages.extend(batch)
                print(f"  {lang}: {len(batch)} pages")
            except Exception as exc:  # one bad language must not kill the run
                print(f"  {lang}: FAILED ({exc})")
    return pages


def run() -> None:
    """Fetch and write data/sources/pages.json."""
    pages = fetch_pages()
    out_path = settings.sources_dir / "pages.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(pages, fh, ensure_ascii=False, indent=2)
    print(f"wrote {len(pages)} pages -> {out_path}")


if __name__ == "__main__":
    run()
