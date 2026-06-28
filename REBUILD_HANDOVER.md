# Integreat Compass — Pipeline Rebuild Handover

> Working doc for the context-first pipeline rebuild. Spec-driven (GitHub Spec Kit).
> Branch: `feature/pipeline-rebuild` (off `main`). Do NOT touch `main` until tested.
> **Status: Phase 0 COMPLETE & committed (`e69cc35`). Resume at Phase 1.**

---

## 0. Quick orientation

- **Repo:** `/Users/harsh/Desktop/AI4Good/AI-powered-immigration-guidance-system`
- **What it is:** Journey-based immigration guidance web app for migrants in Germany (Munich-first). NOT a generic chatbot.
- **Stack:** FastAPI + Python backend (`backend/src/`), TanStack Start + React + Tailwind + shadcn frontend (`frontend/`).
- **LLM:** OpenAI-compatible via `backend/src/core/llm.py` (single `complete()` entry point). `.env` at repo root has `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` (gitignored).
- **RAG:** ChromaDB, 6451 chunks from 3050 Integreat pages (de/en/ar/uk/fa) at `data/sources/index/`. Already built — do NOT re-index.
- **Python venv:** `.venv-api` at repo root (has all deps incl. chromadb, sentence-transformers, httpx, beautifulsoup4, pytest).

### How to run
```bash
# Backend
cd <repo> && . .venv-api/bin/activate && uvicorn api.main:app --app-dir backend/src --port 8000
# Frontend
cd <repo>/frontend && npm run dev   # :8080
# Tests (pytest config is relative to backend/)
. .venv-api/bin/activate && cd backend && python -m pytest -q
# Frontend typecheck
cd frontend && npx tsc --noEmit
```

### Why we're rebuilding
Current pipeline: `message → router → curated journey graph OR dynamic agent → RAG → dump`.
The LLM never asks "do I understand this person?" — it pattern-matches to a journey or
fires retrieval and throws a wall of text + raw sources at the user. We want a
**context-first** loop: understand first, then answer (calibrated length), minimal
sources, optional consent-gated specialist agents, trusted web fetch as RAG supplement.

---

## 1. Constitution (v1.0, locked)

### Core Principles
- **I. Context Before Answers** — never answer before understanding the user's situation. More questions > wrong assumptions. No limit on clarifying questions.
- **II. Privacy-First, Device-Local** — all session data (history, facts, slots) lives only on the user's device (localStorage). No server-side storage. Agent activation needs explicit consent.
- **III. Grounded Responses Only** — every factual claim backed by RAG or a trusted web fetch. Never invent procedures/deadlines/documents/fees. If sources don't cover it, say so + offer a human.
- **IV. Conversational, Not Bureaucratic** — warm, natural tone (knowledgeable friend, not a gov portal). Answer length calibrated to the question; the system decides, not a hardcoded rule.
- **V. Routing is Invisible** — journey routing is internal context enrichment only. Never surfaced as raw data, source lists, or nav labels.
- **VI. Trusted Sources Only** — web fetches restricted to a curated whitelist. No open-web crawl.
- **VII. Agent Consent Gate** — specialist agents suggested proactively but only activate with explicit user consent. Never auto-activate.

### Constraints
- All work on `feature/pipeline-rebuild`; merge to main only after testing confirmed.
- Device-local storage only (localStorage) — no new server-side persistence.
- Teammate's mutagents plug in via the consent gate — we build the gate, NOT the agents.
- Hackathon timeline — prioritise P1 stories for a working demo.

### Governance
- No server-side storage of personal data without explicit sign-off.
- No answer generated without at least one retrieval attempt (RAG or web fetch).
- Agent activation: user consent required, no exceptions.

---

## 2. Specification (v1.0, locked)

### User Stories

**US1 — Context-First Conversation + Full History (P1) 🎯 MVP**
User describes situation in free text. System asks focused clarifying questions — as many as needed — until it genuinely understands, before answering. Full conversation history (all turns) stored on device, passed to LLM every turn (token-capped).
- *Independent test:* "I want to find a flat" → system asks 2-3 targeted follow-ups before answering. Turn 4 correctly uses context from turn 1.
- *Acceptance:* (1) vague msg → clarifying question, never a dump; (2) follow-up uses prior history; (3) reload restores history from localStorage.

**US2 — Adaptive Answer + Minimal Sources Popup (P1) 🎯 MVP**
Answer calibrated to the question — 1 sentence for simple, checklist for procedural. LLM decides format. Sources appear as a subtle "Sources" link at the bottom of the answer card; click opens a small popup with title + URL only; click-outside closes it.
- *Independent test:* "what is Anmeldung?" → 1-2 sentences. "how do I register my address?" → numbered checklist. Both show Sources link; popup shows title+URL only; click-outside dismisses.
- *Acceptance:* (1) simple → ≤3 sentences, no checklist; (2) procedural → checklist; (3) click Sources → popup title+URL only; (4) click outside → closes; (5) no sources → no link.

**US3 — Free Text Welcome, No Chips (P1) 🎯 MVP**
Welcome screen is a single text input + warm prompt ("Hey, what do you need help with?"). No journey chips.
- *Independent test:* fresh load shows no chips, only text input. Type anything → context flow begins.
- *Acceptance:* (1) fresh session → no chips, just input + prompt; (2) any message → context-gathering begins.

**US4 — Agent Consent Gate (P2)**
After a substantive answer in a relevant domain, system proactively suggests a specialist agent ("I can also help you find real listings and prepare messages to landlords — want me to?"). User taps → consent card (what it does + what data) → confirm fires agent (`requires_agent: true` + `agent_id`); decline continues normally.
- Agent candidates for demo: `housing_finder` (listings + landlord messages), `appointment_booker` (Bürgerbüro slots), `document_checker` (docs you have vs. need). LLM decides which (if any) fits the conversation.
- *Acceptance:* (1) post-housing answer → housing suggestion chip; (2) tap → consent card; (3) confirm → `requires_agent:true`, `agent_id:"housing_finder"`; (4) decline → continues, no activation; (5) non-housing convo → no housing agent.

**US5 — Trusted Web Fetch Supplement (P2)**
When RAG returns low-confidence/zero results, fetch from relevant whitelisted domains to supplement. Fetched content cited as a source.
- *Acceptance:* (1) RAG 0 results + whitelisted-domain topic → fetch + use; (2) off-whitelist URL → never fetched; (3) successful fetch → appears as source in popup.

### Functional Requirements
- FR-001 ask clarifying questions before answering when ambiguous
- FR-002 pass full conversation history to LLM every turn
- FR-003 store history in localStorage on device
- FR-004 answer length/format decided by LLM, not hardcoded
- FR-005 sources shown only as title+URL in dismissable popup — no excerpts to user
- FR-006 welcome screen no chips — free text only
- FR-007 journey routing internal — never surfaced
- FR-008 agent activation requires explicit consent — never auto
- FR-009 web fetch only whitelisted domains
- FR-010 Lyra-crafted system prompt for context gathering
- FR-011 all session data on device
- FR-012 graceful degrade — if fetch/RAG fail, acknowledge uncertainty not invent

### Success Criteria
- SC-001 vague opener → ≥1 clarifying question before answer
- SC-002 turn-4 follow-up references turn-1 context
- SC-003 simple <3 sentences; procedural → checklist
- SC-004 sources popup opens on click, closes on click-outside, no excerpts
- SC-005 welcome loads with zero chips
- SC-006 reload restores full history
- SC-007 agent suggestion after relevant convo; tap → consent card
- SC-008 out-of-RAG question → whitelisted web fetch when applicable

### Key decisions (locked during clarify)
- **Context-gathering threshold:** LLM judges each turn ("do I know enough?"). No minimum-question counter. The Lyra prompt does the heavy lifting.
- **History cap:** sliding window, token-capped, **oldest turns dropped first**. `MAX_HISTORY_TOKENS = 4000` (~38 turns ≈ 19 back-and-forths; ~$0.04/turn extra on GPT-4o, negligible on mini). Tune later.
- **Agent suggestion:** LLM decides which agent from conversation context.
- **Lyra prompt:** written/generated during implementation (task T008), not pre-baked.
- **Welcome copy:** minimal/chill, e.g. "Hey, what do you need help with?"

### Edge cases
- History overflow → drop oldest turns first (token budget).
- "hi"/"thanks" mid-convo → warm conversational reply, don't reset context.
- RAG + web both empty → acknowledge uncertainty, offer human handoff.
- Decline agent then re-ask later → re-offer, no penalty.
- Whitelisted domain unreachable → fall back to RAG-only + uncertainty note.

---

## 3. Implementation Plan (v1.0)

### Cost/feasibility research (resolved blockers)
- **HTML fetch:** `httpx` + `beautifulsoup4` already installed. All whitelist domains are server-rendered HTML — no headless browser needed. Plan: httpx (async) + BS4 to strip nav/footer/scripts, truncate to ~2000 tokens/page, UA header + 10s timeout.
- **History cap:** 4000 tokens chosen (see above). Avg turn ≈ 103 tokens.

### Constitution check: all ✅ (no violations in the plan).

### Architecture (target)
```
backend/src/
├── core/
│   ├── llm.py              (unchanged — single complete() entry point)
│   ├── types.py            (Phase 0 ✅ done)
│   └── config.py           (Phase 0 ✅ done)
├── orchestration/
│   ├── context_engine.py   (NEW — context-gathering loop, LLM judgment)
│   ├── agent_suggester.py  (NEW — decides which agent to suggest post-answer)
│   └── pipeline.py         (rebuilt around context_engine)
└── retrieval/
    ├── web_fetch.py         (NEW — whitelisted domain fetcher)
    └── search.py            (unchanged)

frontend/src/
├── lib/
│   ├── session.ts          (extend: full history save/load, token-aware trim)
│   └── types.ts            (Phase 0 ✅ done)
├── hooks/
│   └── use-compass.ts      (extend: history state, agent consent handling)
└── components/compass/
    ├── WelcomeScreen.tsx   (rebuilt: no chips, text input + chill prompt)
    ├── AnswerCard.tsx       (extend: sources popup, agent suggestion chip)
    ├── SourcesPopup.tsx     (NEW — click-to-open, click-outside-to-close)
    └── AgentConsentCard.tsx (NEW — consent UI before agent activation)
```

### Decisions & rationale
| Decision | Why | Rejected |
|---|---|---|
| LLM judges context sufficiency | flexible, handles unforeseen edge cases | min-question counter (too rigid) |
| Full history, token-capped 4k | covers 38 turns, fits context window | summarisation (extra call, no demo benefit) |
| Lyra prompt written manually | faster, controllable | auto-gen mid-session (unpredictable) |
| Agent suggestions LLM-decided post-answer | natural, context-aware | hardcoded per journey (breaks dynamic) |
| Trusted-domain whitelist in config | easy extend, auditable | regex open-web filter (risky) |
| Sources popup (click to open) | unobtrusive | inline sources (clutter) |

---

## 4. Tasks / Phases

### Phase 0 — Branch + Foundation ✅ DONE (commit `e69cc35`)
- [x] T001 branch `feature/pipeline-rebuild`
- [x] T002 `core/types.py` — `ConversationTurn`, `Session.history`, `AgentSuggestion`, `ChatResponse.agent_suggestion` + `requires_agent`, `ChatRequest.agent_id`
- [x] T003 `core/config.py` — `MAX_HISTORY_TOKENS=4000`, `TRUSTED_DOMAINS` (10 domains)
- [x] T004 `frontend/src/lib/types.ts` — mirror all type changes (+ fixed mock.ts literals)
- Note: T013 (history on ChatRequest) NOT needed separately — history flows via `session.history` which is already in `ChatRequest.session`.
- Verified: 28 backend tests pass, `tsc --noEmit` clean.

### Phase 1 — US3 Free Text Welcome ✅ DONE (commit `51d2930`)
- [x] T005 `WelcomeScreen.tsx` — centred warm prompt + single text input, no chips
- [x] T006 `use-compass.ts` — removed cold-start bootstrap API call; welcome is client-side
- [x] T007 `pipeline.py` — cold-start returns empty options; test updated
- Verified: no chips on load, no POST /chat on load, typing starts conversation.

### Phase 2 — US1 Context-First + Full History ✅ DONE (commits `c3ac612`, `5c2fe9d`, `b109314`)
- [x] T008 Lyra-optimised system prompt in `context_engine.py` (4-question checklist, JSON-first, 3 few-shot examples, GPT-5.5/o-series tuned)
- [x] T009 `orchestration/context_engine.py` (NEW) — `run_turn(message, history, facts, registry)` → `{action:"ask"}` OR `{action:"answer", query_for_rag, facts_extracted}`
- [x] T010 `lib/session.ts` — `trimHistoryToTokenBudget(history, maxTokens=4000)` dropping oldest first
- [x] T011 `use-compass.ts` — `pendingMessageRef` tracks user msg; `applyResponse` appends user+assistant turns; `loadSession` rebuilds UI turns on reload
- [x] T012 `orchestration/pipeline.py` — free-text path replaced: context_engine → ask OR `_render_free_text_answer()` (direct RAG); engine failure → handoff
- [x] `llm.py` — added optional `messages` param for multi-turn history (backward-compatible)
- [x] `use-compass.ts` — clears `journey_id/stage_id/dynamic` on load so stale navigation never hijacks context-engine path
- Verified (SC-001 ✓): "I need help" → "What do you need help with — housing, registration...?"
- Verified (SC-002 ✓): follow-up "register my address in Munich" → grounded answer referencing Munich without re-asking
- Verified (SC-006 ✓): Cmd+R restores full conversation from localStorage
- Note: RAG requires `.venv-api/bin/uvicorn` (not system uvicorn) — chromadb only in venv Python
- Note: duplicate text in answer bubble (short_answer shown twice) — fixed in Phase 3 T016

### Phase 3 — US2 Adaptive Answer + Sources Popup ✅ DONE (commit `0dacd3b`)
- [x] T014 `retrieval/answer_generator.py` — adaptive system prompt: LLM picks format by complexity (≤3 sentences for simple, numbered steps for procedural); last-6 history turns included for personalisation.
- [x] T015 `SourcesPopup.tsx` (NEW) — "Sources (N)" pill; click → floating panel title+URL only; click-outside closes via useEffect + ref.
- [x] T016 `AnswerCard.tsx` — removed `short_answer` (already in chat bubble); removed inline sources; wired SourcesPopup; returns null when card has nothing to show.
- [x] T017 `pipeline.py` — strips `excerpt` in `_respond()` before `ChatResponse` (excerpt is internal RAG grounding only, FR-005).
- Verified (SC-003 ✓): procedural question → numbered steps; simple question → ≤3 sentences, no steps card.
- Verified (SC-004 ✓): Sources pill appears; popup shows title+URL only; click-outside closes.
- 28/28 backend tests pass; tsc clean. Pushed to remote.

### Phase 4 — US4 Agent Consent Gate ✅ DONE (commits `3faded2`, `a51ca0c`, `09eee9c`)
- [x] T018 `orchestration/agent_suggester.py` (NEW) — LLM picks agent from `housing_finder`/`appointment_booker`/`document_checker` using RAG query as topic signal; logs decision at WARNING so it's visible in uvicorn.
- [x] T019 `pipeline.py` — calls suggester after grounded answers (guard: sources non-empty); handles `req.agent_id` consent confirm → `requires_agent: True`.
- [x] T020 `AgentConsentCard.tsx` (NEW) — label, description, data_needed, Confirm / Not now buttons.
- [x] T021 `use-compass.ts` + `ChatThread.tsx` — `agentSuggestion` on Turn type; `confirmAgent` clears card + fires send; `declineAgent` clears locally. Props wired through index.tsx.
- Verified (SC-007 ✓): housing query → "Find real listings" card appears; Confirm/Decline both work.
- Gotcha: `answer.uncertainty` being non-null (partial source coverage) was blocking suggest() — fixed by removing that guard; only empty sources blocks it.
- Gotcha: `log.info` not visible in uvicorn by default — use `log.warning` for agent_suggester decisions.

### Phase 5 — US5 Trusted Web Fetch (P2)
- [ ] T022 `retrieval/web_fetch.py` (NEW) — `fetch(query, domains) -> list[Source]`; httpx + BS4 clean, title+URL.
- [ ] T023 `pipeline.py` — after RAG, if `len(sources)<2` or low confidence, call web_fetch w/ TRUSTED_DOMAINS; merge.
- **Checkpoint:** low-RAG question pulls whitelisted domain; appears in popup; off-whitelist never fetched.

### Phase 6 — Polish
- [ ] T024 E2E test all 5 stories manually
- [ ] T025 update `PROGRESS.md`
- [ ] T026 open PR `feature/pipeline-rebuild` → `main`

### Execution order
Phase 0 ✅ → Phase 1 → Phase 2 → Phase 3 (in order; context engine before answer gen rewire) → Phases 4 & 5 (parallel-safe after 3) → Phase 6.

---

## 5. Current state
- Branch `feature/pipeline-rebuild`. Phases 0–4 complete. **Resume at Phase 5 (teammate) → Phase 6.**
- Latest commits: `09eee9c` (agent_suggester fix), `3faded2` (Phase 4), `0dacd3b` (Phase 3), `c3ac612` (Phase 2 core).
- `main` is untouched. The rebuild replaces the free-text entry path; curated journeys + dynamic_journey remain for option_id routing.
- 28 backend tests pass; frontend tsc clean; working tree clean.

### How to run
```bash
# Backend — must use venv uvicorn directly (chromadb only in .venv-api)
.venv-api/bin/uvicorn api.main:app --app-dir backend/src --port 8000 --reload
# Frontend
cd frontend && npm run dev   # :8080
# Tests
.venv-api/bin/python -m pytest -q --rootdir backend backend
# Typecheck
cd frontend && npx tsc --noEmit
```

## 6. Important gotchas
- `gpt-5.5`/o-series reject `temperature` → `llm.py` already retries without it. If answers silently fall back to handoff, check logs for "retrieval failed".
- **Always use `.venv-api/bin/uvicorn`** — system uvicorn doesn't have chromadb. Check with `.venv-api/bin/python -c "import chromadb; print('ok')"`.
- pytest must run from `backend/` (pythonpath/testpaths are relative there).
- `Session.history` is required in TS now — any new Session literal needs `history: []`.
- Free-text pipeline tests mock `context_engine.run_turn` — do NOT mock `llm.complete` for those.
- Phase 3 known issue to fix: `short_answer` shows twice (once as bubble text, once in AnswerCard) — T016 removes the AnswerCard duplicate.
- Don't re-index RAG. Don't commit `.env` / `data/sources/index/` / `.venv-api`.
