---
editor_options: 
  markdown: 
    wrap: 72
---

# Integreat Compass — Technical Design Report

## 1. What it is

Integreat Compass is a multilingual AI assistant that helps refugees and
immigrants navigate German bureaucracy. A user types (or speaks) a
question in their own language and receives a grounded, step-by-step
answer drawn from the Integreat migrant-guidance content base, with
citable sources, reasoning trace, and an optional hand-off to a human
counselor.

------------------------------------------------------------------------

## 2. High-Level Architecture

```         
Browser (React 19)
  │  HTTPS / SSE
  ▼
FastAPI  (port 8000)
  ├── /chat/stream  ──►  Pipeline  ──►  Router
  │                                      ├── Curated Journey Graph
  │                                      └── LangGraph Agent
  │                                             ├── search_official_info → ChromaDB (RAG)
  │                                             ├── search_web           → DuckDuckGo
  │                                             ├── ask_user
  │                                             ├── provide_answer
  │                                             └── escalate_to_human
  └── /transcribe   ──►  OpenAI STT (gpt-4o-mini-transcribe)
```

The frontend and backend are completely decoupled: the frontend sends
the full session state with every request; the backend is stateless. No
server-side session store.

------------------------------------------------------------------------

## 3. Backend

### 3.1 Entry Point — `backend/src/api/main.py`

FastAPI application with three endpoints:

| Endpoint | Method | Purpose |
|------------------------|------------------------|------------------------|
| `/health` | GET | Returns `{status: ok, journeys: [...]}` |
| `/chat` | POST | Blocking turn (non-streaming fallback) |
| `/chat/stream` | POST | Server-Sent Events: reasoning steps live, then final answer |
| `/transcribe` | POST | Multipart audio → transcript via OpenAI STT |

The journey registry (`data/journeys/*.json`) is loaded once at startup
via `load_journeys()`. Adding a new journey JSON file and restarting is
enough to make it available — no code change required.

### 3.2 Pipeline — `backend/src/orchestration/pipeline.py`

`run_turn()` / `run_turn_stream()` is the runtime loop for a single
conversation turn. Decision tree (in order):

1.  **Human handoff explicitly requested** → `_handoff()`
2.  **Option tap matches a curated journey** → enter/re-enter that
    journey graph
3.  **Session has an active dynamic (LLM-planned) journey** →
    `dynamic_journey.run()`
4.  **Free-text with no active journey** → create `DynamicState`, pass
    to `dynamic_journey.run()`
5.  **Cold start (no message, no journey)** → welcome screen + journey
    chips

`run_turn_stream()` checks the same conditions but delegates to
`dynamic_journey.run_stream()` for the agent path, yielding SSE events
as the agent thinks. For curated journey turns (chips, handoff) it
yields only the final response — so the frontend uses one streaming
endpoint for everything.

### 3.3 Router — `backend/src/orchestration/router.py`

Maps a free-text message onto known journey IDs. Two paths:

-   **Primary (LLM):** sends the message + journey catalog to the LLM;
    returns a JSON with `journey_ids` and `extracted_slots` (city,
    language, urgency). Gated — the LLM can only pick from known IDs.
-   **Fallback (no API key):** embedding cosine-similarity between the
    message and each journey's `intent_examples`. If the best score is
    below 0.15 the message matches nothing (welcome screen).

### 3.4 Curated Journey Graph — `backend/src/orchestration/graph_engine.py`

Journey templates live in `data/journeys/*.json`. Each template is a DAG
of *stages*:

-   **Slot stages** — ask for a missing value (city, visa type, etc.) as
    tappable chips
-   **Content stages** — retrieve and generate a grounded answer using
    retrieval
-   **Escalation conditions** — slot values that re-route (e.g.
    `urgency=high` → crisis journey)
-   **Transitions** — the next stage to advance to once all slots are
    filled

The pipeline walks this graph one stage per turn until it reaches a
terminal content stage or hands off to a human. A cycle guard
(`_MAX_HOPS = 20`) prevents authoring errors from looping forever.

There are 9 curated journeys: `address_registration`,
`arrival_first_steps`, `german_course`, `health_insurance`,
`housing_search`, `human_counseling`, `school_childcare`,
`urgent_crisis`, `work_ausbildung`

### 3.5 LangGraph Agent — `backend/src/orchestration/agent_graph.py`

Used for all free-text messages that don't match a curated journey (or
continue an in-progress dynamic journey). A tool-calling agent loop:

```         
START → agent (LLM, tool_choice="required")
          ↕ tool calls
        tools node
          → END when a terminal tool is called (ask_user / provide_answer / escalate)
```

**Five tools:**

| Tool | Purpose |
|------------------------------------|------------------------------------|
| `search_official_info` | RAG over the Integreat corpus (ChromaDB) |
| `search_web` | DuckDuckGo fallback for city-specific live details |
| `ask_user` | Ask ONE clarifying question with 2–5 tappable options |
| `provide_answer` | Emit the final structured answer (rejected if no sources retrieved) |
| `escalate_to_human` | Hand off to a human counselor |

Guards: - `tool_choice="required"` forces a structured call every step —
no free-prose responses - `provide_answer` is rejected if no sources
have been retrieved yet (prevents hallucination) - `ask_user` is
rejected if fewer than 2 options are provided (enforces options-first
UX) - Max 4 searches per turn and max 10 agent/tool cycles (latency
cap) - Duplicate queries are detected and skipped

The streaming variant (`stream_agent`) yields step events (`thinking`,
`search`, `search_result`, `error`, `reviewing`, `ask`, `answer`,
`handoff`) as they happen, which the frontend renders as a live
reasoning trace.

### 3.6 Retrieval — `backend/src/retrieval/`

**Index (`index.py`):** ChromaDB persistent vector store at
`data/sources/index/`. Chunks of 900 characters with 150-character
overlap. Each chunk stores full page metadata (title, URL, last_updated,
language, available_languages).

**Embeddings (`embeddings.py`):** `intfloat/multilingual-e5-large` — a
cross-lingual model that matches queries in any language to content in
any language.

**Search (`search.py`):** Semantic retrieval with re-ranking.
Over-fetches `k×4` candidates, then boosts by language match (+0.05) and
city mention (+0.03), deduplicates by page, and returns the top-k.

**Answer generator (`answer_generator.py`):** Calls the LLM with a
strict system prompt (no facts outside the provided sources) and asks
for a structured `StructuredAnswer` (short_answer + typed sections:
steps, checklist, contact, list, note) in the user's language.

**Faithfulness check (`faithfulness_check.py`):** Post-generation pass
that verifies every claim in the answer can be traced to a source.
Strips or flags anything that can't.

**Web search (`web_search.py`):** DuckDuckGo adapter used by the agent
when the corpus doesn't cover something.

### 3.7 Data Model — `backend/src/core/types.py`

```         
ChatRequest
  message          : str | None       # free text
  option_id        : str | None       # tapped chip
  session          : Session | None   # full client wallet, echoed each turn
  attachment       : Attachment | None

Attachment
  name             : str
  mime_type        : str
  base64           : str | None       # image files
  text             : str | None       # text files

Session
  journey_id       : str | None
  stage_id         : str | None
  slots            : dict             # city, language, visa_type, etc.
  completed_stages : list[str]
  dynamic          : DynamicState | None

DynamicState
  goal             : str
  roadmap          : list[str]
  step_index       : int
  history          : list[dict]       # [{role, content}] — conversation memory
  facts            : dict

ChatResponse
  assistant_message
  options          : list[Option]     # tappable chips
  answer           : StructuredAnswer | None
  sources          : list[Source]
  privacy_receipt  : PrivacyReceipt
  requires_handoff : bool
  handoff_summary  : HandoffSummary | None
  roadmap / roadmap_step              # visible progress for dynamic journeys
  session          : Session          # echoed back for client to persist
```

### 3.8 Configuration — `backend/src/core/config.py`

All model and provider settings are environment-driven (`.env` at repo
root):

| Variable | Default | Purpose |
|------------------------|------------------------|------------------------|
| `LLM_API_KEY` | — | OpenAI-compatible API key |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Swap to vLLM / Ollama for self-hosted |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | Embedding model |
| `STT_MODEL` | `gpt-4o-mini-transcribe` | Speech-to-text model |
| `INTEGREAT_REGION` | `testumgebung-frag-integreat` | Integreat content region |

`settings.llm_external` is `True` when the LLM endpoint is not localhost
— the privacy receipt exposes this to the user.

------------------------------------------------------------------------

## 4. Frontend

### 4.1 Stack

-   **React 19** + **TanStack Router** (file-based routing)
-   **Tailwind CSS v4** with shadcn/ui components
-   **Vite** dev server (port 8090)
-   No Redux / Zustand — all state in a single `useCompass` hook

### 4.2 State — `frontend/src/hooks/use-compass.ts`

The `useCompass` hook owns all conversation state:

```         
turns       : Turn[]          # rendered chat bubbles
options     : Option[]        # current tappable chips
session     : Session | null  # the client wallet (also in localStorage)
status      : idle | loading | error
steps       : ReasoningStep[] # live agent trace (streaming)
```

Key callbacks: - `sendText(text, attachment?)` — appends a user turn,
calls `streamChat()` - `selectOption(opt)` — taps a chip, calls
`streamChat()` - `setLanguage(lang)` — updates session slot, flips
`document.dir` for RTL, persists to localStorage - `startOver()` —
clears session and localStorage

Session is loaded from `localStorage` on mount. Only the session object
is persisted — conversation history is client-side memory, not stored
server-side.

### 4.3 API Layer — `frontend/src/lib/api.ts`

Three functions:

-   `streamChat(req, handlers)` — POSTs to `/chat/stream`, consumes SSE
    frames, fires `onStep` for reasoning events and `onDone` for the
    final response. Falls back to `postChat()` on network error.
-   `postChat(req)` — blocking POST to `/chat` (non-streaming fallback)
-   `transcribeAudio(blob)` — multipart POST to `/transcribe`, returns
    transcript string

`VITE_USE_MOCK=true` routes all calls to a local mock instead of the
real backend (used for demo/offline mode).

### 4.4 Components

| Component | Purpose |
|------------------------------------|------------------------------------|
| `Header` | App title, language switcher (8 languages), Start Over |
| `WelcomeScreen` | Landing: headline, 4 quick-start chips, free-text input |
| `ChatThread` | Scrollable list of `Turn` bubbles |
| `AnswerCard` | Renders a `StructuredAnswer` (sections: steps, checklist, contact, list, note) |
| `ReasoningTrace` | Live agent step timeline (streams open, collapses to "Thought for Xs" when done) |
| `FreeTextInput` | Text input with voice (mic) and file attachment |
| `OptionQuestionCard` | Agent clarifying questions rendered as tappable chips + optional free-text |
| `SourcesPopup` | Citable sources panel, expandable from the answer |
| `PrivacyReceipt` | Shows which slots were used, where stored, whether data left the device |
| `HandoffPanel` | Editable counselor summary shown when `requires_handoff = true` |
| `ErrorRetry` | Error state with retry button |

### 4.5 Internationalisation — `frontend/src/lib/translations.ts`

18 UI strings × 8 languages: English, German, Arabic, Farsi, Ukrainian,
Russian, Turkish, French.

RTL support (Arabic, Farsi) is implemented with: -
`document.documentElement.dir = "rtl"` on language switch — flips the
entire page - Tailwind CSS logical properties throughout (`ps-`, `pe-`,
`ms-`, `me-`, `start-`, `end-`) so layout mirrors automatically with no
conditional class logic

### 4.6 File Attachment

When a user attaches a file: - **Images** → read as base64 via
`FileReader.readAsDataURL`, sent as `{base64, mime_type}` - **Text
files** → read with `FileReader.readAsText`, sent as `{text, mime_type}`

On the backend, images become OpenAI vision `image_url` content blocks
in the conversation history; text files are prepended as a labelled
block before the user's message. Both flow through the same
`dynamic_journey._prepare()` function.

### 4.7 Voice Input

The `FreeTextInput` component records audio via the `MediaRecorder` API
with a 250 ms timeslice (ensures chunks are collected even for short
utterances). On stop, the blob is sent to `/transcribe` and the
transcript fills the text input. Errors (permission denied, empty blob,
transcription failure) are shown as visible red text below the input.

------------------------------------------------------------------------

## 5. Data Flow: A Single Turn

```         
User types "How do I get health insurance?" and taps Send
  │
  ▼
useCompass.sendText()
  ├── Appends user Turn to turns[]
  └── Calls streamChat({message, session})
        │
        ▼
      POST /chat/stream
        │
        ▼
      pipeline.run_turn_stream()
        ├── Session has no journey_id and message is present
        ├── Creates DynamicState(goal="How do I get health insurance?")
        └── Delegates to dynamic_journey.run_stream()
              │
              ▼
            agent_graph.stream_agent()
              ├── [event: thinking]        → frontend shows "Thinking…"
              ├── Tool: search_official_info("health insurance Germany newcomer")
              ├── [event: search]          → frontend shows "Searching official content"
              ├── ChromaDB returns 5 sources
              ├── [event: search_result, count: 5]
              ├── [event: thinking]
              ├── Tool: ask_user("Are you employed or a student?", options=[...])
              ├── [event: ask]
              └── [event: done] → ChatResponse with options chips
        │
        ▼
      Frontend renders OptionQuestionCard with chips
        User taps "Employed"
        │
        ▼
      Next turn: session.dynamic.history now has [user, assistant, user]
      Agent searches again with city context, calls provide_answer
      [event: done] → ChatResponse with StructuredAnswer + Sources
        │
        ▼
      AnswerCard rendered with steps, checklist, sources popup
      ReasoningTrace collapses to "Thought for 8s · 4 steps"
```

------------------------------------------------------------------------

## 6. Privacy Model

-   **No server-side session storage** — the session wallet (`slots`,
    `dynamic.history`, `completed_stages`) travels in every request and
    is echoed back in every response. The client persists it in
    `localStorage`.
-   **Conversation history on device** — `dynamic.history` (the LLM
    conversation memory) is stored only in the session, never in a
    database.
-   **Privacy receipt** — every response includes a `PrivacyReceipt`
    listing which slots were read, where data is stored, and whether the
    turn used an external LLM (data left the device boundary). The UI
    shows this to the user.
-   **Human handoff is consent-gated** — when `requires_handoff = true`,
    the frontend shows an editable `HandoffSummary` which the user
    reviews before sharing with a counselor.

------------------------------------------------------------------------

## 7. Deployment

-   **Backend:** FastAPI + uvicorn. Docker image at
    `backend/Dockerfile`. CI/CD via GitHub Actions deploying to EC2 via
    SSM.
-   **Frontend:** Vite build served statically (or via the TanStack
    Start server).
-   **Environment:** `.env` at repo root controls all model/provider
    settings. Swap `LLM_BASE_URL` to a localhost vLLM/Ollama endpoint
    for fully self-hosted, privacy-preserving deployment.
-   **Index:** ChromaDB persisted at `data/sources/index/`. Built once
    with `python -m retrieval.index` from the 3,050 Integreat pages
    (6,451 chunks).

------------------------------------------------------------------------

## 8. Key Design Decisions

| Decision | Rationale |
|------------------------------------|------------------------------------|
| Stateless backend | No session store to maintain; full history in session wallet means any server instance can handle any turn |
| `tool_choice="required"` on the agent | Guarantees structured output (options chips, grounded answer) — no free-prose responses that bypass the UX contract |
| `provide_answer` rejected without sources | Prevents the model from answering from training data; forces a real retrieval step |
| Tailwind logical properties for RTL | One set of CSS, no conditional classes — `dir` attribute does the mirroring |
| 250 ms MediaRecorder timeslice | Without a timeslice, `onstop` fires with a single chunk that may be 0 bytes on some browsers |
| Session in localStorage (not cookies) | No third-party tracking surface; data is local by design and disclosed in the privacy receipt |
| Journey registry from JSON files | Non-engineers can author new curated journeys by dropping a file; no deploy needed for content changes |
