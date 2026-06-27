
# Progress Tracker

Live status for [PROTOCOL.md](PROTOCOL.md). **Update your own rows as you work.**
Status: `TODO` · `DOING` · `DONE` · `BLOCKED`. Keep notes short; put detail in commits/PRs.

**Last updated:** 2026-06-27 — Frontend (D1–D7) built via Lovable + integrated on `track-d-frontend` (Harsh). Owners swapped: Harsh→Frontend, Xavier→Engine.

---

## Snapshot

| Track                     | Owner   | Status | Branch                |
| ------------------------- | ------- | ------ | --------------------- |
| 0. Foundation & contracts | Harsh   | DONE   | `main` (do first)   |
| A. Orchestration + API    | Xavier  | DONE   | `track-a-engine`    |
| B. Retrieval / RAG        | Daril   | TODO   | `track-b-retrieval` |
| C. Journey content        | Shampoo | TODO   | `track-c-journeys`  |
| D. Frontend               | Harsh   | DOING  | `track-d-frontend`  |
| E. Eval + pitch           | Shampoo | TODO   | `track-e-eval`      |

**Milestones:** M1 ⬜ · M2 ⬜ · M3 ⬜ · M4 (MVP) ⬜ · M5 (MVP) ⬜

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

➡️ **Phase 0 on `main` (pending commit). Tracks A–E can start.**
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
| A6 | Real`/chat` pipeline                | DONE   | `orchestration/pipeline.py`; live. Content path degrades gracefully until B3–B5 land |
| A7 | Handoff generator                     | DONE   | minimal summary, no transcript; surfaced via `handoff_summary` |

**22/22 tests pass** (`cd backend && .venv/bin/python -m pytest`). Live `/chat` verified.

## Track B — Retrieval / RAG (Daril)

| ID | Task                                  | Status | Notes                    |
| -- | ------------------------------------- | ------ | ------------------------ |
| B1 | Ingest Integreat →`pages.json`     | TODO   |                          |
| B2 | Index +**Arabic→German proof** | TODO   | log the test result here |
| B3 | `search()`                          | TODO   |                          |
| B4 | `generate_answer()`                 | TODO   |                          |
| B5 | `check()` faithfulness              | TODO   |                          |

## Track C — Journey content (Shampoo)

| ID     | Task                                       | Status | Notes                   |
| ------ | ------------------------------------------ | ------ | ----------------------- |
| C1     | `arrival_first_steps.json`               | TODO   |                         |
| C2     | `address_registration.json` (demo spine) | TODO   |                         |
| C3     | `german_course.json`                     | TODO   |                         |
| C4–C8 | health / school / housing / work / crisis  | TODO   | stretch                 |
| C9     | `human_counseling.json`                  | TODO   | needed for handoff demo |
| C-val  | all validate + load via A1                 | TODO   |                         |

## Track D — Frontend (Xavier)

| ID | Task                             | Status | Notes    |
| -- | -------------------------------- | ------ | -------- |
| D1 | API client + types               | DONE   | `src/lib/api.ts` (single fetch) + `types.ts` exact snake_case match |
| D2 | Chat thread                      | DONE   | `ChatThread.tsx`, auto-scroll, typing indicator |
| D3 | Option chips                     | DONE   | `OptionChips.tsx`, primary input, 48px, accent for `human` |
| D4 | Structured answer card + sources | DONE   | `AnswerCard.tsx`, freshness badges, uncertainty row |
| D5 | Privacy receipt                  | DONE   | `PrivacyReceipt.tsx` accordion |
| D6 | Local wallet (localStorage)      | DONE   | `session.ts`, key `compass_session`, SSR-safe |
| D7 | Handoff panel + consent gate     | DONE   | `HandoffPanel.tsx`, consent-gated share |
| D8 | Flip to real backend             | TODO   | set `VITE_API_URL`, `VITE_USE_MOCK=false`; needs A6 live |

## Track E — Eval + pitch (Shampoo / Harsh)

| ID | Task                           | Status | Notes      |
| -- | ------------------------------ | ------ | ---------- |
| E1 | `test_questions.csv`         | TODO   |            |
| E2 | Comparison table               | TODO   | needs A6+B |
| E3 | Pitch deck (`docs/pitch.md`) | TODO   |            |

---

## Blockers

_None yet. Add: `[ID] — what's blocked — who can unblock`._

## Integration log

_Append dated lines as seams connect, e.g. `2026-06-27 18:00 — frontend ↔ mock /chat green (M1)`._

- 2026-06-27 — Phase 0 pushed: mock `/chat` returns valid §4.1 JSON; frontend builds green. Tracks A–E unblocked.
- 2026-06-27 — Track A complete: real pipeline live, 22 tests green. A6 calls the
  retrieval seam (B3–B5) and **degrades gracefully** (answer "pending") until B lands —
  so the moment Daril pushes B, the address-registration journey is end-to-end (M3).

## Decisions made mid-build

- **Import root.** PROTOCOL §4 mixed `uvicorn backend.src.api.main:app` (F1) with
  `from core.types import` (F2) — not both literally possible. Chose **`backend/src`
  as the import root** (`from core...`, `from retrieval...`). Run with
  `--app-dir backend/src`. No `from backend.src...` anywhere.
- **Phase-0 deps split.** `pyproject` has an `api` extra (no torch) so the
  API/mock boots without the heavy retrieval ML stack. Track B installs the full set.
- **Contract addition (§4.1): `handoff_summary`.** A7 produces a counselor summary
  but §4.1 had nowhere to carry it. Added an **optional** `ChatResponse.handoff_summary`
  (null unless `requires_handoff`). Backward-compatible; mirrored in
  `frontend/lib/types.ts`. **Xavier (D7):** render it editable, consent-gated.
- **Router offline fallback.** A4 uses the LLM when `LLM_API_KEY` is set, else a
  deterministic keyword matcher over `intent_examples` — keeps the dev loop and
  tests working without a key; upgrades automatically when a key is present.
