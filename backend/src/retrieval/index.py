"""Track B (Daril) — Build the persistent multilingual vector index.

Embeds ``title + excerpt + content`` (chunked) with ``settings.embed_model`` into
a persistent ChromaDB at ``data/sources/index/``. Each chunk keeps full page
metadata so retrieval can cite it. Public API (seam, PROTOCOL.md Track B-B2):

    build_index() -> None
    get_collection()

CLI:  python -m retrieval.index [--rebuild] [--proof]
"""
from __future__ import annotations

import json
from functools import lru_cache

from core.config import settings
from retrieval.embeddings import embed_passages, embed_queries  # noqa: F401 (re-export)

COLLECTION_NAME = "integreat_pages"


def _pages_path():
    return settings.sources_dir / "pages.json"


@lru_cache(maxsize=1)
def get_collection():
    """Return the persistent Chroma collection used by search()."""
    import chromadb

    client = chromadb.PersistentClient(path=str(settings.index_dir))
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def _chunk(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Split long content into overlapping, boundary-aware windows."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        window = text[start:end]
        brk = max(window.rfind("\n\n"), window.rfind(". "))
        if brk > size * 0.5 and end < len(text):
            end = start + brk + 1
        chunks.append(text[start:end].strip())
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def build_index(batch_size: int = 256) -> None:
    """Embed data/sources/pages.json into ChromaDB with full metadata."""
    with open(_pages_path(), encoding="utf-8") as fh:
        pages = json.load(fh)

    col = get_collection()
    existing = col.get(include=[])  # idempotent rebuild
    if existing["ids"]:
        col.delete(ids=existing["ids"])

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    for page in pages:
        body = page.get("content") or page.get("excerpt") or ""
        chunks = _chunk(body) or ([page["title"]] if page.get("title") else [])
        for i, chunk in enumerate(chunks):
            doc = f"{page.get('title','')}\n{page.get('excerpt','')}\n{chunk}".strip()
            ids.append(f"{page['language']}-{page['id']}-{i}")
            docs.append(doc)
            metas.append(
                {
                    "page_id": page["id"],
                    "title": page.get("title", ""),
                    "url": page.get("url") or "",
                    "last_updated": page.get("last_updated") or "",
                    "language": page["language"],
                    "excerpt": page.get("excerpt", "") or chunk[:300],
                    "available_languages": json.dumps(
                        page.get("available_languages") or {}
                    ),
                }
            )

    total = 0
    for s in range(0, len(docs), batch_size):
        sl = slice(s, s + batch_size)
        col.add(
            ids=ids[sl],
            embeddings=embed_passages(docs[sl]),
            documents=docs[sl],
            metadatas=metas[sl],
        )
        total += len(docs[sl])
        print(f"  indexed {total}/{len(docs)} chunks")
    print(f"done: {total} chunks from {len(pages)} pages -> {settings.index_dir}")


def _anmeldung_family_urls(anchor_slug: str = "wohnsitz-anmelden") -> set[str]:
    """URLs of the Anmeldung page AND all its translations (cross-lingual proof)."""
    with open(_pages_path(), encoding="utf-8") as fh:
        pages = json.load(fh)
    by_id = {p["id"]: p for p in pages}
    anchor = next(
        (p for p in pages if p["language"] == "de" and anchor_slug in (p["url"] or "")),
        None,
    )
    if not anchor:
        return set()
    family = {anchor["id"], *(anchor.get("available_languages") or {}).values()}
    return {by_id[i]["url"] for i in family if i in by_id and by_id[i].get("url")}


def proof(query: str = "تسجيل العنوان", language: str = "ar", k: int = 5) -> bool:
    """B2 acceptance test: an Arabic query retrieves the Anmeldung page (any lang)."""
    from retrieval.search import search

    family = _anmeldung_family_urls()
    results = search(query, city=None, language=language, k=k)
    print(f"\n[{language}] query: {query!r}  (target = Anmeldung page family)")
    hit = False
    for i, s in enumerate(results, 1):
        is_target = s.url in family
        hit = hit or is_target
        print(f"  {i}. [{s.language}] {s.title}{'  <-- TARGET' if is_target else ''}")
    print(f"PROOF {'PASS' if hit else 'FAIL'}: Anmeldung page in top-{k}: {hit}")
    return hit


if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 chokes on ar/cyrillic
    except Exception:
        pass

    if get_collection().count() == 0 or "--rebuild" in sys.argv:
        build_index()
    if "--proof" in sys.argv:
        proof()
