# Integreat Compass — Pitch

> **Journey-based, source-grounded immigration guidance — in the newcomer's own language.**

---

## 1. One-liner

A migrant opens a chat, types *"I just arrived"* in any language, and is guided
step-by-step through real bureaucratic journeys — every answer grounded in live,
official Integreat content, with a privacy receipt and a one-tap human handoff.

## 2. The problem

Newcomers face a maze of German bureaucracy (Anmeldung, Krankenversicherung,
Kita, Integrationskurs…) in a language they don't yet speak. A generic chatbot
makes this **worse**, not better — we measured it (§4):

- Answers an **English** question **in German**.
- Gives **US healthcare advice** ("Healthcare.gov, Medicaid") to *"How do I get
  health insurance?"* — the user is in Munich.
- Gives **Ukrainian** school-enrollment steps to a Ukrainian newcomer who needs
  the **Munich** process.
- Invents steps with **no source and no freshness** — dangerous for legal deadlines.

## 3. Our solution

Three principles, enforced in code (a product **constitution**):

1. **Source-grounded.** Every step/document/deadline comes from a real Integreat
   page, cited with title + URL + `last_updated`. No source ⇒ no claim.
2. **Options-first.** The system clarifies with tappable chips before answering —
   bounded, safe navigation instead of open-ended hallucination.
3. **Privacy by minimization.** Personal data lives in the user's browser (a
   "Personal Data Wallet"); the server is stateless w.r.t. personal data; every
   turn shows a **privacy receipt**; escalation to a human is **consent-gated**.

**Live demo:** *"I am in Munich. I need Kita Anmeldung and Deutschkurs. Answer in
Arabic."* → multi-intent split → options-first journey → grounded answers in
Arabic citing Munich's `kita finder+` and Integrationskurs pages → privacy
receipt → optional human handoff.

## 4. We measured it (eval, `data/eval/comparison.md`)

10 real questions (incl. Arabic Kita+Deutschkurs, Ukrainian school, urgent
housing, multi-intent) through **generic LLM** vs **Integreat Compass**:

| | Generic LLM | Integreat Compass |
|---|---|---|
| Right language | ✗ often German for EN/UK queries | ✓ answers in the user's language (ar, uk, en) |
| Right country/city | ✗ US/Ukraine answers | ✓ Munich-specific (kita finder+, Agentur für Arbeit München) |
| Sources + freshness | ✗ none | ✓ live Integreat pages w/ `last_updated` |
| Hallucinated steps | ✗ invents procedure | ✓ grounded or escalates |
| Urgent case | ✗ generic text | ✓ safe human **handoff**, no fabricated answer |
| Multi-intent | ✗ blends both | ✓ splits & sequences (asks which first) |

## 5. The privacy story — Personal Data Wallet

The `session` (city, language, answers) is persisted in **localStorage** and sent
back per turn as minimal context. The backend keeps **no** personal data. Each
response includes a `privacy_receipt` (`used_fields` / `stored_fields` / `storage`
/ `human_shared`). Handing off to a counselor produces an **editable, consent-gated
summary** — never a raw transcript.

## 6. Generalizability — journeys ship on day one

A journey is **one JSON file**. The engine directory-scans `data/journeys/` at
startup — **drop a file in, restart, it appears. No code, no config.** We shipped
**9 journeys** this way (arrival, address registration, German course, childcare/
school, health insurance, housing, work/Ausbildung, urgent crisis, human
counseling). A new city or topic is an authoring task, not an engineering one.
The retrieval is region-driven (`INTEGREAT_REGION`) — point it at another city and
the content follows.

## 7. Architecture (built parallel, contract-first)

```
Frontend (Next.js)  ──POST /chat──▶  Orchestration (router → graph → slots)
   localStorage wallet                         │
   options-first UI                            ▼
                                     Retrieval (RAG): search → generate → faithfulness
                                            multilingual embeddings over Integreat
```

- **Swappable models.** LLM + embeddings are OpenAI-compatible and env-driven —
  cloud today (`text-embedding-3-small`, `gpt-4o-mini`), **fully self-hosted OSS
  tomorrow** (`multilingual-e5-large`, Qwen/Llama) by changing one env var. Matters
  for a privacy-sensitive public-sector deployment.
- **Verified:** 3050 Integreat pages / 6451 chunks indexed; Arabic query retrieves
  the German Anmeldung page (cross-lingual); 22/22 backend tests green.

## 8. What's next

Document drafting/form-fill support · reranking for sharper citations · self-hosted
open model swapped in (TEE narrative) · follow-up/progress tracking across sessions ·
IndexedDB wallet · the remaining stretch journeys polished.
