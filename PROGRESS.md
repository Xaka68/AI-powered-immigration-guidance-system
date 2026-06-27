# Progress Tracker

Live status for [PROTOCOL.md](PROTOCOL.md). **Update your own rows as you work.**
Status: `TODO` · `DOING` · `DONE` · `BLOCKED`. Keep notes short; put detail in commits/PRs.

**Last updated:** 2026-06-27 (initial) — _edit this line when you change something._

---

## Snapshot

| Track | Owner | Status | Branch |
|---|---|---|---|
| 0. Foundation & contracts | Harsh | TODO | `main` (do first) |
| A. Orchestration + API | Harsh | TODO | `track-a-engine` |
| B. Retrieval / RAG | Daril | TODO | `track-b-retrieval` |
| C. Journey content | Shampoo | TODO | `track-c-journeys` |
| D. Frontend | Xavier | TODO | `track-d-frontend` |
| E. Eval + pitch | Shampoo | TODO | `track-e-eval` |

**Milestones:** M1 ⬜ · M2 ⬜ · M3 ⬜ · M4 (MVP) ⬜ · M5 (MVP) ⬜

---

## Phase 0 — Foundation (Harsh, BLOCKING)

| ID | Task | Status | Notes |
|---|---|---|---|
| F1 | Python project + config | TODO | |
| F2 | Shared types (`core/types.py`) | TODO | |
| F3 | Swappable LLM client | TODO | |
| F4 | Journey schema + `_example.json` | TODO | |
| F5 | Mock `/chat` | TODO | unblocks frontend |
| F6 | Stub modules w/ signatures | TODO | unblocks A & B |
| F7 | Frontend scaffold + `.env.example` | TODO | |

➡️ **When F1–F7 are on `main`, post here and tell the team. Tracks A–E start.**

---

## Track A — Orchestration + API (Harsh)

| ID | Task | Status | Notes |
|---|---|---|---|
| A1 | Journey loader (dir-scan registry) | TODO | |
| A2 | Graph engine (transitions/escalation) | TODO | |
| A3 | Slot manager | TODO | |
| A4 | Router (multi-intent, gated) | TODO | |
| A5 | Slot filler (chips from template) | TODO | |
| A6 | Real `/chat` pipeline | TODO | needs B3–B5 |
| A7 | Handoff generator | TODO | |

## Track B — Retrieval / RAG (Daril)

| ID | Task | Status | Notes |
|---|---|---|---|
| B1 | Ingest Integreat → `pages.json` | TODO | |
| B2 | Index + **Arabic→German proof** | TODO | log the test result here |
| B3 | `search()` | TODO | |
| B4 | `generate_answer()` | TODO | |
| B5 | `check()` faithfulness | TODO | |

## Track C — Journey content (Shampoo)

| ID | Task | Status | Notes |
|---|---|---|---|
| C1 | `arrival_first_steps.json` | TODO | |
| C2 | `address_registration.json` (demo spine) | TODO | |
| C3 | `german_course.json` | TODO | |
| C4–C8 | health / school / housing / work / crisis | TODO | stretch |
| C9 | `human_counseling.json` | TODO | needed for handoff demo |
| C-val | all validate + load via A1 | TODO | |

## Track D — Frontend (Xavier)

| ID | Task | Status | Notes |
|---|---|---|---|
| D1 | API client + types | TODO | |
| D2 | Chat thread | TODO | |
| D3 | Option chips | TODO | |
| D4 | Structured answer card + sources | TODO | |
| D5 | Privacy receipt | TODO | |
| D6 | Local wallet (localStorage) | TODO | |
| D7 | Handoff panel + consent gate | TODO | |
| D8 | Flip to real backend | TODO | needs A6 |

## Track E — Eval + pitch (Shampoo / Harsh)

| ID | Task | Status | Notes |
|---|---|---|---|
| E1 | `test_questions.csv` | TODO | |
| E2 | Comparison table | TODO | needs A6+B |
| E3 | Pitch deck (`docs/pitch.md`) | TODO | |

---

## Blockers

_None yet. Add: `[ID] — what's blocked — who can unblock`._

## Integration log

_Append dated lines as seams connect, e.g. `2026-06-27 18:00 — frontend ↔ mock /chat green (M1)`._

## Decisions made mid-build

_Record any deviation from PROTOCOL.md here so the team stays in sync._
