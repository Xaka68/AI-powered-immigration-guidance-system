# Track B — Retrieval / RAG (Daril)

Source-grounded, multilingual retrieval over real Integreat content. Owns
`backend/src/retrieval/**`. Talks to orchestration only through the signatures in
[PROTOCOL.md §4.3](../../../../PROTOCOL.md); Track A's pipeline imports
`search.search`, `answer_generator.generate_answer`, `faithfulness_check.check`.

## Pipeline

| Step | File | Public function | What it does |
|---|---|---|---|
| B1 | `ingest.py` | `fetch_pages()` / `run()` | Fetch all Integreat pages per language → `data/sources/pages.json`; HTML→text, public URLs, freshness, cross-language links. |
| B2 | `index.py` | `build_index()` / `get_collection()` / `proof()` | Embed (chunked) into persistent ChromaDB; `proof()` = Arabic→German acceptance test. |
| B3 | `search.py` | `search(query, city, language, k)` | Semantic top-k, language/city boost, dedupe per page → `list[Source]`. |
| B4 | `answer_generator.py` | `generate_answer(stage_goal, user_language, sources, slots)` | LLM → `StructuredAnswer` in the user's language, grounded only in sources. |
| B5 | `faithfulness_check.py` | `check(answer, sources)` | Drop/flag unsupported steps/docs; set `uncertainty` when freshness missing. |

`embeddings.py` is the swappable embedding provider (OpenAI now, OSS e5 later via `EMBED_MODEL`).

## Run

Import root is `backend/src` (see `pyproject.toml`), so run with it on `PYTHONPATH`:

```bash
cp .env.example .env            # set LLM_API_KEY (+ EMBED_MODEL=text-embedding-3-small for speed)
pip install -e backend          # or: pip install chromadb sentence-transformers httpx openai beautifulsoup4

PYTHONPATH=backend/src python -m retrieval.ingest        # B1 -> data/sources/pages.json
PYTHONPATH=backend/src python -m retrieval.index --proof # B2 build + Arabic→German proof
```

## Config (env / .env, via `core.config.settings`)

- `EMBED_MODEL` — `text-embedding-3-small` (cloud, fast) or `intfloat/multilingual-e5-large` (OSS). One-var swap.
- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` — used by B4/B5 and (for cloud) embeddings.
- `INTEGREAT_REGION`, `INGEST_LANGUAGES` (env, default `de,en,ar,uk,fa`) — ingestion scope; no city hardcoded.

## Notes / decisions

- URLs rewritten from CMS `admin.integreat-app.de` → public `integreat.app`.
- Chunking ~900 chars with overlap; each chunk carries full page metadata for citation.
- Chroma collection `integreat_pages` at `data/sources/index/` (cosine).
- e5 query/passage prefixes auto-applied when `EMBED_MODEL` contains `e5`.
- OpenAI embeddings are token-budget-batched + retried (non-Latin scripts are token-heavy and hit the 300k-token/req and TPM limits).
- **Verified:** 3050 pages / 6451 chunks indexed; Arabic "تسجيل العنوان" retrieves the Anmeldung page cross-lingually (B2 PASS).
