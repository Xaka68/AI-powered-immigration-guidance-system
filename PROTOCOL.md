# Implementation Protocol

**Project**: Integreat Compass — Journey-Based Immigration Guidance System
**Source of truth**: [spec](specs/001-journey-guidance/spec.md) · [plan](specs/001-journey-guidance/plan.md) · [architecture](docs/architecture.md) · [constitution](.specify/memory/constitution.md)
**Progress tracker**: [PROGRESS.md](PROGRESS.md) — update it as you work.

---

## 1. What we are shipping (MVP definition)

A working web app a migrant can open and be guided through **at least 3 pre-built
journeys** (target: arrival → address registration, German course, health
insurance), in a **non-German language**, where every answer is
**source-grounded** from real Integreat content, navigation is **options-first
(tappable chips)**, and there is a **privacy receipt** and a **human-handoff**
exit.

**MVP is reached when all of these are true:**

1. A user types *"I just came to Germany"* and gets routed into journey options.
2. They can complete the **address-registration** journey end-to-end with real
   Integreat sources (title + URL + `last_updated`) on each answer.
3. A **non-German query** (Arabic/Farsi/Ukrainian) retrieves the right German
   page and answers in the user's language. *(This is the primary path — not an
   edge case. Validate it on day one.)*
4. **At least 3 journeys** load automatically from `data/journeys/` and the
   router can pick between them. Multi-intent ("Kita and Deutschkurs") splits.
5. A risky/uncertain case produces an **editable, consent-gated handoff summary**
   (no raw transcript).
6. The **demo scenario** runs without crashing:
   *"I am in Munich. I need Kita Anmeldung and Deutschkurs. Please answer in Arabic."*

Anything beyond this (all 9 journeys, document drafting, TEE, reranking) is
**stretch**, listed in §7.

---

## 2. The one rule that makes this parallelizable: CONTRACT-FIRST

Generalizability and parallelism both come from the same place: **the three
layers talk only through fixed contracts.**

- **API contract** (`POST /chat` request/response) → seam between **frontend** and **backend**.
- **Journey schema** (`data/journeys/schema.json`) → seam between **engine** and **journey authors**.
- **Module signatures** (`core/types.py` + agreed function defs) → seam between **orchestration** and **retrieval**.

Phase 0 (Harsh, ~1–2h, **blocking**) writes all three contracts plus stub files
and a **mock `/chat`** that returns contract-shaped fake data. The moment Phase 0
is pushed, the other three tracks start in parallel against the mock and the
schema. **Nobody waits for anybody's implementation — only for the contract.**

A new journey later = drop a JSON file in `data/journeys/`. The engine
directory-scans at startup, so **no code change, no config** — that is the
product's generalizability claim and it must stay true.

---

## 3. Ownership map (zero-conflict by construction)

After Phase 0, each person owns a directory **exclusively**. No two people edit
the same file. Integration happens through imports/HTTP, not shared edits.

| Track | Owner | Exclusive paths | Never touches |
|---|---|---|---|
| **0. Foundation** | Harsh | (writes everything once, then stops) | — |
| **A. Orchestration + API** | Harsh | `backend/src/orchestration/**`, `backend/src/api/**`, `backend/src/core/**` | retrieval, frontend, journeys |
| **B. Retrieval / RAG** | Daril | `backend/src/retrieval/**` | orchestration, api, frontend |
| **C. Journey content** | Shampoo | `data/journeys/**` | all code |
| **D. Frontend** | Xavier | `frontend/**` | all backend |
| **E. Eval + pitch** | Shampoo | `data/eval/**`, `docs/pitch.md` | all code |

`backend/src/api/main.py` is owned by Harsh and *imports* Daril's retrieval
functions by their agreed signature — Daril writes the function bodies in his own
files, Harsh writes the one-line import. No collision.

**Git discipline:** one branch per track (`track-a-engine`, `track-b-retrieval`,
`track-c-journeys`, `track-d-frontend`). Rebase on `main` often. Because zones
are disjoint, merges are trivial. Commit small, push often, update PROGRESS.md.

---

## 4. Shared contracts (Phase 0 output — the linchpin)

### 4.1 API contract — `POST /chat`

**Request**
```jsonc
{
  "message": "I found an apartment",   // user free text; omit if option_id set
  "option_id": "has_apartment",        // id of a tapped chip; omit if free text
  "session": {                          // echoed back from previous response; null on first turn
    "journey_id": "address_registration",
    "stage_id": "housing_status",
    "slots": { "city": "Munich", "language": "ar", "housing_status": null },
    "completed_stages": ["orientation"]
  }
}
```

**Response**
```jsonc
{
  "journey_id": "address_registration",
  "stage_id": "documents",
  "assistant_message": "string, rendered in the user's language",
  "options": [                          // tappable chips for the next decision; [] if none
    { "id": "missing_landlord_confirmation", "label": "I don't have landlord confirmation" },
    { "id": "talk_to_human", "label": "Talk to a counselor" }
  ],
  "answer": {                           // null until a content stage is reached
    "short_answer": "string",
    "next_steps": ["string", "string"],
    "documents_needed": ["string"],
    "uncertainty": "string or null"
  },
  "sources": [
    { "title": "...", "url": "...", "last_updated": "2025-03-01", "language": "de" }
  ],
  "privacy_receipt": {
    "used_fields": ["city", "housing_status"],
    "stored_fields": [],
    "storage": "local",                 // local | session | none
    "human_shared": false
  },
  "requires_handoff": false,
  "session": { /* updated session object; client persists this in localStorage */ }
}
```

**Invariants (constitution-enforced):**
- `answer.next_steps`/`documents_needed` MUST be derivable from `sources`. No source ⇒ no procedural claim.
- If freshness is missing, `uncertainty` MUST say the date couldn't be verified.
- `options` is the primary input. Free text is the fallback, funneled back to options.
- `session` never leaves the client except as minimal per-turn context; server is stateless w.r.t. personal data.

### 4.2 Journey schema — `data/journeys/schema.json`

Authoring a journey = writing one JSON file to this shape. **No code, no source
URLs** (retrieval is semantic at runtime via `retrieval_query`).

```jsonc
{
  "id": "address_registration",
  "title": "Register my address (Anmeldung)",
  "description": "Guidance for registering a Munich address after moving in.",
  "intent_examples": ["I found an apartment", "I need to register", "Anmeldung", "wohnung anmelden"],
  "stages": [
    {
      "id": "housing_status",
      "type": "eligibility_context",          // one of the 8 stage types (data-model.md)
      "goal": "Find out whether the user already has an apartment",
      "required_slots": ["housing_status"],
      "retrieval_query": "address registration Anmeldung requirements documents",
      "option_sets": [
        {
          "slot": "housing_status",
          "prompt": "Do you already have an apartment?",
          "options": [
            { "id": "has_apartment", "label": "Yes, I have one" },
            { "id": "looking",       "label": "Still looking" },
            { "id": "temporary",     "label": "Temporary accommodation" }
          ],
          "free_text_fallback": true
        }
      ],
      "next_stage_rules": [
        { "if_slot": "housing_status", "equals": "has_apartment", "go_to": "documents" },
        { "if_slot": "housing_status", "equals": "looking",       "go_to": "ROUTE:housing_search" },
        { "if_slot": "housing_status", "equals": "temporary",     "go_to": "ROUTE:housing_search" }
      ],
      "escalation_exits": [
        { "condition": "slot:urgency == high", "go_to": "ROUTE:human_counseling" }
      ]
    }
  ]
}
```

- `go_to` values: a `stage_id` in this journey, `ROUTE:<journey_id>` to jump
  journeys, or `HANDOFF` to escalate.
- Stage `type` ∈ `orientation | eligibility_context | action_plan | documents |
  appointment_contact | translation_communication | follow_up | human_handoff`.
- A content stage (e.g. `action_plan`, `documents`) needs a `retrieval_query`;
  a pure routing/clarification stage may omit it.

### 4.3 Module signatures (Python, the orchestration ↔ retrieval seam)

```python
# backend/src/core/types.py  (Pydantic models — Harsh, Phase 0)
class Source(BaseModel):
    title: str; url: str; last_updated: str | None; language: str; excerpt: str
class StructuredAnswer(BaseModel):
    short_answer: str; next_steps: list[str]; documents_needed: list[str]; uncertainty: str | None

# backend/src/core/llm.py  (swappable, OpenAI-compatible — Harsh, Phase 0)
def complete(system: str, user: str, json_schema: dict | None = None) -> str | dict: ...
#   reads LLM_BASE_URL + LLM_API_KEY from env so we can swap cloud→self-hosted open model later.

# backend/src/retrieval/search.py        (Daril)
def search(query: str, city: str | None, language: str, k: int = 5) -> list[Source]: ...
# backend/src/retrieval/answer_generator.py  (Daril)
def generate_answer(stage_goal: str, user_language: str, sources: list[Source], slots: dict) -> StructuredAnswer: ...
# backend/src/retrieval/faithfulness_check.py (Daril)
def check(answer: StructuredAnswer, sources: list[Source]) -> StructuredAnswer: ...
```

---

## 5. Tasks

Status legend in PROGRESS.md: `TODO / DOING / DONE / BLOCKED`.
`[P]` = parallel-safe with everything else in its phase.

### PHASE 0 — Foundation & Contracts · Owner: **Harsh** · BLOCKING (~1–2h)

> Until F1–F7 are pushed to `main`, nobody else can start cleanly. Do this first.

- **F1 — Python project + config.** `backend/pyproject.toml` (FastAPI, uvicorn,
  httpx, chromadb, sentence-transformers, pydantic, python-dotenv, openai).
  `backend/src/core/config.py` reads env: `LLM_BASE_URL`, `LLM_API_KEY`,
  `LLM_MODEL`, `EMBED_MODEL` (default `intfloat/multilingual-e5-large`),
  `INTEGREAT_REGION` (default `testumgebung-frag-integreat`).
  *Accept:* `uvicorn backend.src.api.main:app` boots.

- **F2 — Shared types.** `backend/src/core/types.py` — Pydantic models for
  `Source`, `StructuredAnswer`, `Option`, `OptionSet`, `PrivacyReceipt`,
  `Session`, `ChatRequest`, `ChatResponse` exactly matching §4.1.
  *Accept:* `from core.types import ChatResponse` works; models serialize to §4.1 JSON.

- **F3 — Swappable LLM client.** `backend/src/core/llm.py` — `complete()` per
  §4.3, OpenAI-compatible; supports a `json_schema` arg for structured output.
  *Accept:* a smoke call returns text; a schema call returns a parsed dict.

- **F4 — Journey schema + reference.** `data/journeys/schema.json` (§4.2) and
  `data/journeys/_example.json` (one complete 2-stage example). Add a short
  `data/journeys/README.md` telling authors how to write a journey.
  *Accept:* `_example.json` validates against `schema.json`.

- **F5 — Mock `/chat`.** `backend/src/api/main.py` — `POST /chat` returns a
  **hardcoded** `ChatResponse` (contract-shaped) so the frontend can build
  immediately. Also `GET /health`.
  *Accept:* `curl -XPOST /chat` returns valid §4.1 JSON.

- **F6 — Stub modules with signatures.** Create every file Tracks A/B will own,
  each with the agreed signature and a `raise NotImplementedError` or a tiny
  mock: `orchestration/{loader,graph_engine,slot_manager,router,slot_filler,handoff_generator}.py`,
  `retrieval/{ingest,index,search,answer_generator,faithfulness_check}.py`.
  *Accept:* all import without error; signatures match §4.3.

- **F7 — Frontend scaffold + env.** `frontend/` Next.js app (TypeScript) with a
  single page and a typed API client pointing at the mock `/chat`. Root
  `.env.example` documenting all env vars.
  *Accept:* `npm run dev` renders a page that calls the mock and shows the reply.

**Phase-0 checkpoint:** push to `main`. Announce in PROGRESS.md. Tracks A–E start.

---

### TRACK A — Orchestration Engine + API · Owner: **Harsh** · `backend/src/orchestration/`, `backend/src/api/`

- **A1 — Journey loader.** `loader.py`: scan `data/journeys/*.json` at startup,
  validate against `schema.json`, build an in-memory registry
  `{journey_id: Journey}`. Ignore `_*.json`. **Directory-scan = the
  zero-config generalizability mechanism — keep it dynamic.**
  *Depends:* F4. *Accept:* dropping a new valid JSON makes it appear after restart with no code change.

- **A2 — Graph engine.** `graph_engine.py`: given `(journey, stage_id, slots)`
  → resolve current stage, compute missing `required_slots`, evaluate
  `escalation_exits`, and on slot completion apply `next_stage_rules`
  (incl. `ROUTE:` and `HANDOFF`). Pure, unit-testable, no LLM.
  *Depends:* A1. *Accept:* deterministic transitions for the address-registration graph.

- **A3 — Slot manager.** `slot_manager.py`: merge newly extracted/selected slots
  into session, expose "what's still missing for this stage".
  *Depends:* F2. *Accept:* slot round-trips through `Session`.

- **A4 — Router.** `router.py`: LLM intent classifier that maps free text onto
  the **loaded journey set** (use each journey's `intent_examples`). Returns
  ranked `journey_ids[]` (multi-intent) + any `extracted_slots` (city,
  language, urgency, child-age…). **Gated to known journeys — never invents
  one.** *Depends:* A1, F3. *Accept:* "Kita and Deutschkurs" → `[school_childcare, german_course]`.

- **A5 — Slot filler.** `slot_filler.py`: when A2 reports a missing slot, emit
  the `option_sets` chips from the journey template (not LLM-generated).
  *Depends:* A2. *Accept:* missing `housing_status` → the 3 chips from the JSON.

- **A6 — Real `/chat` pipeline.** Replace F5 mock: `router → graph_engine →
  slot check → (if content stage) retrieval.search + generate_answer +
  faithfulness.check → assemble ChatResponse + privacy_receipt`. Build the
  privacy receipt from which slots were read this turn.
  *Depends:* A2–A5, B3–B5. *Accept:* address-registration journey runs end-to-end against real retrieval.

- **A7 — Handoff generator.** `handoff_generator.py`: when `requires_handoff`,
  produce `{user_goal, known_context, sources_consulted, open_questions,
  urgency}` from session — **no raw transcript**. *Depends:* A6.
  *Accept:* risky case yields a minimal summary object; sharing stays blocked until consent (UI gate in D7).

---

### TRACK B — Retrieval / RAG · Owner: **Daril** · `backend/src/retrieval/`

- **B1 — Ingest.** `ingest.py`: fetch all pages for `INTEGREAT_REGION` from
  `https://cms.integreat-app.de/<region>/<lang>/wp-json/extensions/v3/pages/`,
  normalize each to `{id, title, url, content (HTML→text), excerpt,
  last_updated, language, parent_id, available_languages}` → `data/sources/pages.json`.
  Pull `de` + `en` + at least one non-Latin language (ar). **No city hardcoded.**
  *Depends:* F1. *Accept:* `pages.json` has hundreds of pages with freshness + language fields.

- **B2 — Index + multilingual proof.** `index.py`: embed `title + excerpt +
  content` with `EMBED_MODEL` (multilingual-e5-large / BGE-m3) → persistent
  ChromaDB at `data/sources/index/`, metadata = all normalized fields.
  **Then immediately test an Arabic query retrieves the correct German page and
  log the result in PROGRESS.md.** *Depends:* B1. *Accept:* Arabic "تسجيل العنوان" returns the Anmeldung page.

- **B3 — Search.** `search.py::search()` per §4.3: semantic top-k over Chroma,
  filter/boost by `city` and prefer pages whose `available_languages` includes
  the user language; return `Source[]` with freshness. *Depends:* B2.
  *Accept:* returns relevant, citable sources for a stage `retrieval_query`.

- **B4 — Answer generator.** `answer_generator.py::generate_answer()`: prompt the
  LLM with stage goal + retrieved sources + slots → `StructuredAnswer` in the
  user's language. **System prompt forbids any claim not in the sources and
  forbids inventing steps/deadlines/documents.** *Depends:* B3, F3.
  *Accept:* output cites only retrieved pages; answers in target language.

- **B5 — Faithfulness check.** `faithfulness_check.py::check()`: second LLM pass
  (or rule pass) that drops/flags any `next_step`/`document` not supported by
  the sources; sets `uncertainty` when freshness is missing. *Depends:* B4.
  *Accept:* an unsupported claim injected into a test answer gets stripped or flagged.

---

### TRACK C — Journey Content · Owner: **Shampoo** · `data/journeys/`

> Pure authoring against `schema.json` (§4.2). Use `_example.json` as a template.
> **No invented bureaucracy** — only steps that real Integreat pages can ground
> (coordinate with Daril: if a step has no source, it's a handoff, not a claim).
> **MVP needs C1–C3 done well.** C4–C9 are stretch; rough them in if time allows.

- **C1 — `arrival_first_steps.json`** — orientation → needs_assessment →
  priority_routing. The "I just arrived" entry point that `ROUTE:`s into others.
- **C2 — `address_registration.json`** — orientation → housing_status →
  anmeldung_steps → documents → edge_cases → handoff. **This is the demo spine.**
  Edge branches: `missing_landlord_confirmation`, `no_appointment`, `form_help_requested`.
- **C3 — `german_course.json`** — orientation → eligibility → course_types → enrollment → handoff.
- **C4 — `health_insurance.json`** *(stretch)* — employment_status → insurance_type → registration → handoff.
- **C5 — `school_childcare.json`** *(stretch)* — child_age → kita/school → enrollment → documents → handoff.
- **C6 — `housing_search.json`** *(stretch)* — housing_type → resources → edge_cases → handoff.
- **C7 — `work_ausbildung.json`** *(stretch)*.
- **C8 — `urgent_crisis.json`** *(stretch)* — immediate `HANDOFF`.
- **C9 — `human_counseling.json`** — consent → summary → handoff (small; needed for A7/D7 demo).
- **C-validate** — every file validates against schema and loads via A1; the
  demo scenario's two intents (Kita + Deutschkurs) are covered.

---

### TRACK D — Frontend · Owner: **Xavier** · `frontend/`

> Build entirely against the **mock `/chat`** (F5) until A6 lands. Then flip the
> base URL. **Options-first** is the core UX — chips before free text.

- **D1 — API client + types.** TS types mirroring §4.1; `postChat(req)` helper;
  base URL from env. *Depends:* F7. *Accept:* typed round-trip to mock.
- **D2 — Chat thread.** Alternating user/assistant bubbles; renders `assistant_message`. `[P]`
- **D3 — Option chips.** Render `options[]` as buttons; click sends `{option_id, session}`. Primary input. `[P]`
- **D4 — Structured answer card.** `short_answer`, `next_steps`, `documents_needed`,
  and **source links with `last_updated` freshness badge**; show `uncertainty` note when present. `[P]`
- **D5 — Privacy receipt.** Collapsible drawer from `privacy_receipt` — what was used/stored and where. `[P]`
- **D6 — Local wallet.** Persist `session` in `localStorage` (the Personal Data
  Wallet story); send it back each turn; never send more than the contract. `[P]`
- **D7 — Handoff panel + consent gate.** When `requires_handoff`, show editable
  summary fields; "Share with counselor" disabled until a consent checkbox is ticked. *Depends:* D1.
- **D8 — Flip to real backend.** Point base URL at A6; verify full journey. *Depends:* A6.

---

### TRACK E — Eval + Pitch · Owner: **Shampoo** (Harsh assists on running) · `data/eval/`, `docs/pitch.md`

- **E1 — Test set.** `data/eval/test_questions.csv` — the 10 questions from the
  handover (incl. Arabic Kita+Deutschkurs, urgent housing, multi-intent). `[P]`
- **E2 — Comparison table.** Run each through the system; record generic-vs-
  journey-guided answer, sources hit, hallucination?, clarification asked?,
  actionable?. *Depends:* A6 + B. This is the "we measured it" judging slide.
- **E3 — Pitch deck.** `docs/pitch.md` → slides: one-liner, problem, live demo,
  eval table, **Personal Data Wallet** privacy story, generalizability ("journeys
  ship on day one; a new one is just a file"), what's next.

---

## 6. Integration milestones

| ID | Milestone | Needs | Proves |
|---|---|---|---|
| **M1** | Mock end-to-end | F5+F7, D2–D3 | UI ↔ contract works |
| **M2** | Real retrieval answers one query | B1–B4 | grounding + multilingual |
| **M3** | One full journey (address reg.) live | A6 + C2 + B + D8 | the core loop |
| **M4** | Multi-journey + multilingual demo | A4 + C1–C3 + M3 | **MVP** |
| **M5** | Handoff + privacy receipt + eval | A7 + D5 + D7 + E2 | MVP polish |

**MVP = M4 + M5.**

---

## 7. Stretch (only after MVP)

Document drafting/form support · all 9 journeys polished · reranking ·
self-hosted open model swapped in · IndexedDB wallet · TEE narrative ·
follow-up/progress tracking across sessions.

---

## 8. Constitution guardrails (apply to every task)

1. **No invented procedure.** Steps/deadlines/documents come from sources or the
   authored graph — never the LLM. Unsupported ⇒ uncertainty or handoff.
2. **Source-grounded.** Every material claim carries title + URL + freshness.
3. **Options-first.** Chips before free text wherever the next branch is known.
4. **Privacy by minimization.** Ask only what the current step needs; default
   session/local; server stateless w.r.t. personal data; show the receipt.
5. **Safe escalation.** Consent-gated, editable handoff summary; no raw transcript.
