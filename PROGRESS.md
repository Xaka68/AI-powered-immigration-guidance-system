
# Progress Tracker

Live status for [PROTOCOL.md](PROTOCOL.md). **Update your own rows as you work.**
Status: `TODO` · `DOING` · `DONE` · `BLOCKED`. Keep notes short; put detail in commits/PRs.

**Last updated:** 2026-06-27 — Tracks B (retrieval) + C (journeys) complete and verified; E1 done (Daril, covering Shampoo).

---

## Snapshot

| Track                     | Owner   | Status | Branch                |
| ------------------------- | ------- | ------ | --------------------- |
| 0. Foundation & contracts | Harsh   | DONE   | `main` (do first)   |
| A. Orchestration + API    | Harsh   | DONE   | `track-a-engine`    |
| B. Retrieval / RAG        | Daril   | DONE   | `daril/tracks-bce`  |
| C. Journey content        | Daril (for Shampoo) | DONE | `daril/tracks-bce` |
| D. Frontend               | Xavier  | TODO   | `track-d-frontend`  |
| E. Eval + pitch           | Daril (for Shampoo) | DONE | `daril/tracks-bce` |

**Milestones:** M1 ⬜ · **M2 ✅** · M3 ⬜ (backend ready; needs D8) · M4 ⬜ (backend ready; needs frontend) · M5 ⬜

---

## Phase 0 — Foundation (Harsh, BLOCKING)

| ID | Task                                | Status | Notes             |
| -- | ----------------------------------- | ------ | ----------------- |
| F1 | Python project + config             | DONE   | pyproject + `core/config.py`; venv boots uvicorn |
| F2 | Shared types (`core/types.py`)    | DONE   | Pydantic == §4.1; imports OK |
| F3 | Swappable LLM client                | DONE   | OpenAI-compatible, env-driven, json mode |
| F4 | Journey schema +`_example.json`   | DONE   | draft-2020-12; `_example.json` validates |
| F5 | Mock`/chat`                       | DONE   | `/health`+`/chat` valid §4.1 JSON (curl-verified) |
| F6 | Stub modules w/ signatures          | DONE   | orchestration+retrieval stubs import clean |
| F7 | Frontend scaffold +`.env.example` | DONE   | Next 14/TS; `npm run build` green; seed page hits mock |

➡️ **Phase 0 on `main`. Tracks A–E started.**
Run: backend `uvicorn api.main:app --app-dir backend/src --port 8000 --reload` ·
frontend `cd frontend && npm install && npm run dev`.

---

## Track A — Orchestration + API (Harsh)

| ID | Task                                  | Status | Notes        |
| -- | ------------------------------------- | ------ | ------------ |
| A1 | Journey loader (dir-scan registry)    | DONE   | validates vs schema; skips `_*`; dup-id guard |
| A2 | Graph engine (transitions/escalation) | DONE   | pure; deterministic; 7 unit tests |
| A3 | Slot manager                          | DONE   | immutable merge; ignores None |
| A4 | Router (multi-intent, gated)          | DONE   | LLM + offline keyword fallback; gated to known ids |
| A5 | Slot filler (chips from template)     | DONE   | chips straight from `option_sets` |
| A6 | Real`/chat` pipeline                | DONE   | `orchestration/pipeline.py`; live, now wired to real retrieval (B) |
| A7 | Handoff generator                     | DONE   | minimal summary, no transcript; surfaced via `handoff_summary` |

**22/22 tests pass** (`cd backend && python -m pytest`). Live `/chat` verified.

## Track B — Retrieval / RAG (Daril) — DONE

| ID | Task                                  | Status | Notes                    |
| -- | ------------------------------------- | ------ | ------------------------ |
| B1 | Ingest Integreat →`pages.json`     | DONE   | `fetch_pages()/run()`; HTML→text, public URLs, freshness, cross-lang links. **3050 pages** (de,en,ar,uk,fa) |
| B2 | Index +**Arabic→German proof** | DONE   | **6451 chunks** in Chroma. **PROOF PASS:** AR `تسجيل العنوان` → "Wohnsitz anmelden / ummelden" (Anmeldung) at rank 1–2 |
| B3 | `search()`                          | DONE   | top-k + language/city boost + per-page dedupe |
| B4 | `generate_answer()`                 | DONE   | grounded `StructuredAnswer` in user's language; forbids unsourced claims |
| B5 | `check()` faithfulness              | DONE   | drops unsupported steps/docs; freshness→uncertainty; offline-safe fallback |

End-to-end verified: AR Anmeldung query → grounded Arabic answer (real docs incl.
Wohnungsgeberbestätigung), faithfulness pass. `embeddings.py` = swappable provider
(OpenAI now / OSS e5 later via `EMBED_MODEL`).

## Track C — Journey content (Daril, for Shampoo) — DONE

| ID     | Task                                       | Status | Notes                   |
| ------ | ------------------------------------------ | ------ | ----------------------- |
| C1     | `arrival_first_steps.json`               | DONE   | router journey → all topical journeys |
| C2     | `address_registration.json` (demo spine) | DONE   | housing_status→documents→(landlord/appointment); edge cases + escalation |
| C3     | `german_course.json`                     | DONE   | residence_status→course_options→enrollment |
| C4–C8 | health / school / housing / work / crisis  | DONE   | health_insurance, school_childcare, housing_search, work_ausbildung, urgent_crisis (immediate HANDOFF) |
| C9     | `human_counseling.json`                  | DONE   | consent→prepare_handoff |
| C-val  | all validate + load via A1                 | DONE   | **9 journeys load**, schema OK, all ROUTE/stage/HANDOFF targets resolve, 11 content stages grounded |

## Track D — Frontend (Xavier)

| ID | Task                             | Status | Notes    |
| -- | -------------------------------- | ------ | -------- |
| D1 | API client + types               | TODO   |          |
| D2 | Chat thread                      | TODO   |          |
| D3 | Option chips                     | TODO   |          |
| D4 | Structured answer card + sources | TODO   |          |
| D5 | Privacy receipt                  | TODO   |          |
| D6 | Local wallet (localStorage)      | TODO   |          |
| D7 | Handoff panel + consent gate     | TODO   | render `handoff_summary` editable/consent-gated |
| D8 | Flip to real backend             | TODO   | needs A6 (ready) |

## Track E — Eval + pitch (Daril, for Shampoo)

| ID | Task                           | Status | Notes      |
| -- | ------------------------------ | ------ | ---------- |
| E1 | `test_questions.csv`         | DONE   | `data/eval/test_questions.csv`, 10 Qs (AR Kita+Deutschkurs, urgent, multi-intent, UK) |
| E2 | Comparison table               | DONE   | `data/eval/run_eval.py` + `comparison.md`. Generic LLM gave **US health advice / Ukraine school steps / wrong language**; ours: right language + Munich sources + freshness + safe handoff |
| E3 | Pitch deck (`docs/pitch.md`) | DONE   | one-liner, problem, eval table, Personal Data Wallet, generalizability, swappable OSS models |

---

## Blockers

_None._

## Integration log

- 2026-06-27 — Phase 0 pushed: mock `/chat` returns valid §4.1 JSON; frontend builds green. Tracks A–E unblocked.
- 2026-06-27 — Track A complete: real pipeline live, 22 tests green.
- 2026-06-27 — **Track B complete (Daril).** 3050 pages ingested, 6451 chunks indexed; Arabic→German proof PASS; B3→B4→B5 produces grounded Arabic answer. Pipeline now returns real content (no longer "pending"). **M2 reached.**
- 2026-06-27 — **Track C complete (Daril, for Shampoo).** 9 journeys authored + validated via loader (M3/M4 are backend-ready; need frontend D8).
- 2026-06-27 — **Track E complete (Daril, for Shampoo).** E2 ran all 10 Qs through real pipeline vs generic LLM — stark contrast (grounding/language/safety). E3 pitch deck written. Backend MVP (B+C+E) done; remaining for full MVP demo = Track D frontend (D1–D8).
- 2026-06-27 — **loader.py encoding fix** (Harsh's file): `read_text()`→`read_text(encoding="utf-8")`. Without it the loader crashed on Windows for any journey with non-Latin (Arabic) content. **Harsh: please keep at merge.**
- 2026-06-27 — **test_pipeline.py** `test_content_stage_degrades_gracefully_without_retrieval` updated to force `NotImplementedError` (B is now wired), so it still tests the fallback offline. All 22 tests still pass. **Harsh: review at merge.**

## Decisions made mid-build

- **Import root.** `backend/src` (`from core...`, `from retrieval...`); run with `--app-dir backend/src`.
- **Phase-0 deps split.** `api` extra (no torch) boots the API without the heavy ML stack.
- **Contract addition (§4.1): `handoff_summary`.** Optional `ChatResponse.handoff_summary`. **Xavier (D7):** render editable, consent-gated.
- **Router offline fallback.** LLM when `LLM_API_KEY` set, else keyword matcher over `intent_examples`.
- **(B) Swappable embeddings.** `EMBED_MODEL=text-embedding-3-small` (OpenAI) for hackathon speed; flip to `intfloat/multilingual-e5-large` for fully-OSS, no code change. OpenAI requests are token-budget-batched + rate-limit-retried (non-Latin scripts are token-heavy → hit 300k-tok/req and TPM limits).
- **(B) URL rewrite.** CMS `admin.integreat-app.de` → public `integreat.app` so cited sources open.
- **(C) Content-stage routing.** The pipeline returns after rendering a content stage, so `next_stage_rules` don't fire there — edge-case follow-ups (e.g. `missing_landlord_confirmation`) route via `escalation_exits` (which can target a stage, `ROUTE:`, or `HANDOFF`).
- **(C) No invented bureaucracy.** Journeys carry only graph structure + `retrieval_query`; all steps/docs come from live Integreat pages at runtime. Unsourced blockers → `HANDOFF`.
