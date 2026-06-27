
# Progress Tracker

Live status for [PROTOCOL.md](PROTOCOL.md). **Update your own rows as you work.**
Status: `TODO` · `DOING` · `DONE` · `BLOCKED`. Keep notes short; put detail in commits/PRs.

**Last updated:** 2026-06-27 — Phase 0 (F1–F7) complete and verified (Harsh).

---

## Snapshot

| Track                     | Owner   | Status | Branch                |
| ------------------------- | ------- | ------ | --------------------- |
| 0. Foundation & contracts | Harsh   | DONE   | `main` (do first)   |
| A. Orchestration + API    | Harsh   | TODO   | `track-a-engine`    |
| B. Retrieval / RAG        | Daril   | TODO   | `track-b-retrieval` |
| C. Journey content        | Shampoo | TODO   | `track-c-journeys`  |
| D. Frontend               | Xavier  | TODO   | `track-d-frontend`  |
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
| A1 | Journey loader (dir-scan registry)    | TODO   |              |
| A2 | Graph engine (transitions/escalation) | TODO   |              |
| A3 | Slot manager                          | TODO   |              |
| A4 | Router (multi-intent, gated)          | TODO   |              |
| A5 | Slot filler (chips from template)     | TODO   |              |
| A6 | Real`/chat` pipeline                | TODO   | needs B3–B5 |
| A7 | Handoff generator                     | TODO   |              |

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
| D1 | API client + types               | TODO   |          |
| D2 | Chat thread                      | TODO   |          |
| D3 | Option chips                     | TODO   |          |
| D4 | Structured answer card + sources | TODO   |          |
| D5 | Privacy receipt                  | TODO   |          |
| D6 | Local wallet (localStorage)      | TODO   |          |
| D7 | Handoff panel + consent gate     | TODO   |          |
| D8 | Flip to real backend             | TODO   | needs A6 |

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

## Decisions made mid-build

- **Import root.** PROTOCOL §4 mixed `uvicorn backend.src.api.main:app` (F1) with
  `from core.types import` (F2) — not both literally possible. Chose **`backend/src`
  as the import root** (`from core...`, `from retrieval...`). Run with
  `--app-dir backend/src`. No `from backend.src...` anywhere.
- **Phase-0 deps split.** `pyproject` has an `api` extra (no torch) so the
  API/mock boots without the heavy retrieval ML stack. Track B installs the full set.
