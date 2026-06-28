# Data Privacy & Minimization

This document explains how Integreat Compass handles personal data, how it meets
the challenge's privacy criteria, and how it compares to Integreat's own chatbot.

## Principles

1. **Personal data stays on the device.** The conversation, the user's situation
   (city, status, visa, etc.), and journey progress live in the browser session
   (the "Personal Data Wallet") — not in a server database.
2. **The server is stateless w.r.t. personal data.** The backend keeps no user
   accounts, no chat history, and no profile store. Each request carries its own
   context; the response hands the updated state back to the client.
3. **Minimize per turn.** Only the context needed to answer the current turn is
   processed. Nothing about the user is persisted server-side.
4. **Be transparent.** Every answer ships a **privacy receipt** showing what was
   used, where it's stored, and whether an external AI provider was involved.
5. **Swappable, self-hostable model.** The LLM is an OpenAI-compatible endpoint
   set by env var, so the whole system can run on a self-hosted open-weight model
   with **no third party** — the same posture as Integreat.

## Where data lives

```
┌─ User's device (browser) ─────────────────────────────┐
│  • conversation history        (session.dynamic)       │   ← the wallet
│  • situation: city, status…    (session.slots/facts)   │
│  • journey progress            (session)               │
│  persisted only in localStorage (lightweight wallet);  │
│  chat history is NOT persisted across reloads.         │
└───────────────────────────────────────────────────────┘
        │ per turn: send ONLY the minimal context needed
        ▼
┌─ Backend (stateless) ─────────────────────────────────┐
│  • no database, no user store, no chat logs            │
│  • runs router → graph → retrieval → answer            │
│  • returns updated session to the client               │
└───────────────────────────────────────────────────────┘
        │ retrieval embeddings: LOCAL (self-hosted e5)
        │ answer generation: LLM endpoint (see below)
        ▼
   LLM endpoint  — self-hosted (nothing leaves) OR external provider (discloses it)
```

What this means in the code:

- **On device:** the `Session` (incl. `dynamic.history`, `slots`) is created/echoed
  by the client. `frontend/src/lib/session.ts` persists only the lightweight wallet
  to `localStorage` and **deliberately drops chat memory**, so a new chat starts
  clean and a previous conversation can never bleed into another.
- **No server persistence:** the backend (`api/main.py`, `orchestration/*`) writes
  no user data to disk or DB, and **logs no message content** (only error codes /
  exception types). Verified: no `open()/write/db` of user data in `api/` or
  `orchestration/`.
- **Embeddings are local:** retrieval runs the multilingual e5 model in-process —
  the user's query is embedded **on the server, not sent to any embedding API**.
- **The only outbound personal data** is the per-turn query/context sent to the
  **LLM endpoint** for answer generation. If that endpoint is external (the demo
  uses OpenAI), the privacy receipt says so; if it's self-hosted, nothing leaves.

## The privacy receipt

Every `/chat` response includes a `PrivacyReceipt` the UI shows under
*"What data was used"*:

| field | meaning |
|---|---|
| `used_fields` | the personal fields used this turn (e.g. `city`, `language`) |
| `stored_fields` | always `[]` — the server stores nothing |
| `storage` | `local` — state lives on the device |
| `human_shared` | `true` only after the user consents to a counselor handoff |
| `external_llm` | `true` if the deployment generates answers with a third-party LLM; `false` if self-hosted |

`external_llm` is derived from `LLM_BASE_URL` (`settings.llm_external`): a
`localhost`/`127.0.0.1` endpoint ⇒ `false` (self-hosted, nothing leaves); any
remote host ⇒ `true` (honest disclosure that data crossed the trust boundary).

## Human handoff

Escalation to a human counselor is **consent-gated**: the agent produces a
**minimal summary** (goal, key context, open questions) — never the raw
transcript — and the user reviews/edits it before anything is shared. `human_shared`
flips to `true` only then.

## How we meet the five criteria

| Criterion | How |
|---|---|
| **Chat-based counseling** | Conversational agent that clarifies → retrieves → answers, with a consent-gated human-counselor handoff. |
| **Very high accuracy** | Answers grounded **only** in retrieved sources (a code guard rejects ungrounded answers); citations + freshness on every claim; clarifies before answering. |
| **Current legal situation** | Grounded in Integreat's curated, human-maintained content (kept current by editors), with source + `last_updated`; uncertain/uncovered cases → handoff, never invented. |
| **Data minimization → on device** | Session/wallet on the device; **stateless server**, no chat logs, no user DB; only minimal per-turn context processed; embeddings run locally; visible privacy receipt. |
| **Open source / open weights / self-hostable** | OpenAI-compatible LLM seam → point `LLM_BASE_URL` at a self-hosted open-weight model (vLLM/Ollama) for a **no-third-party** deployment; embeddings already local/open (e5); retrieval is local. |

## Honest status (demo vs. production posture)

- **Demo:** for convenience the demo points `LLM_MODEL`/`LLM_BASE_URL` at an
  external provider (OpenAI). In that mode the per-turn query is processed
  externally — and the privacy receipt **says so** (`external_llm = true`).
- **Privacy-preserving deployment:** set `LLM_BASE_URL` to a self-hosted
  open-weight model. Then `external_llm = false`, embeddings + retrieval + the
  model all run on infrastructure you control, and **no personal data leaves the
  trust boundary** — matching Integreat's "no third-party LLM services" stance.

## How this compares to Integreat's chatbot

Integreat's `integreat-chat` is **self-hosted, server-side** RAG (OpenSearch +
a local LLM via LiteLLM, *"no third-party LLM services"*), with optional
human-counselor routing (Zammad) per region; their **app** caches *content*
on-device for offline reading, but the **chat itself runs on the server**.

Our posture matches their self-hostable/open stance **and** adds:
**personal data on the device**, a **stateless server** (no chat store), **per-turn
minimization**, and a **visible privacy receipt** — directly answering the brief's
open "store data on end device (?)" question.
