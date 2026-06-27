# Research: Journey-Based Immigration Guidance System

## Decision: Treat Integreat As A "Sign Post," Not A Process Engine

**Rationale**: The Integreat API returns a flat list of pages with `parent.id`
(a chapter -> subpage tree), semantic HTML content, an excerpt, a `last_updated`
timestamp, and `available_languages` with parallel page IDs across ~20 languages.
This gives multilingual, topic-chunked content with a built-in taxonomy for free.
But the content *describes resources* (offices, courses, counseling) — it does
**not** encode the *procedure* of a bureaucratic journey: the ordered steps,
prerequisites, documents, and decision branches. The journey skeletons must
therefore be **hand-authored**; the content layer grounds *what each step says*,
not *which steps exist*. Verifying that a chosen journey's procedure is
reconstructable from available content is a first-hours task, not a discovery to
make late in the build.

**Alternatives considered**:

- **Derive journey steps from Integreat content directly**: Tempting because the
  data is clean, but the procedure is not encoded in it; this would push step
  invention back onto the model and break the accuracy boundary.
- **Author steps with no content binding**: Steps would lack citations and
  freshness, defeating the source-grounding principle.

## Decision: Use Authored Journey Graphs For Multi-Step Bureaucratic Flows

**Rationale**: Migrant-facing guidance can cause real harm if the model invents
steps, deadlines, document requirements, or eligibility rules. Authored journey
graphs let the team curate trusted steps and branch conditions while still
letting the assistant route, translate, explain, and personalize.

**Alternatives considered**:

- **Free-form agent planning**: More dynamic, but too risky for legal and
  municipal procedures.
- **Plain FAQ chatbot**: Easier to build, but does not provide handholding
  through multi-step journeys.
- **Static checklist only**: Safe, but not adaptive enough for different user
  situations and edge cases.

## Decision: Make The Munich Arrival/Housing/Registration Path The First MVP

**Rationale**: This journey is concrete, emotionally relevant, multi-step, and
demonstrates the product's value better than a generic chatbot. It also shows
document preparation, edge cases, privacy controls, and human handoff.

**Alternatives considered**:

- **German course journey**: Lower risk and easier, but less compelling as a
  full handholding demo.
- **Any-topic chatbot**: Broad, but shallow and less defensible.
- **Legal-status journey**: Important, but too sensitive for a first hackathon
  demo without extensive official source coverage.

## Decision: Use Options-First UX As The Default Interaction Model

**Rationale**: Structured choices reduce user burden, help users with limited
German/literacy, and constrain model behavior to trusted branches. Free text
remains available for unexpected needs.

**Alternatives considered**:

- **Free-text chat first**: Familiar, but more error-prone and harder to test.
- **Long profile form**: Collects too much sensitive data before value is clear.

## Decision: Use Lightweight Custom Retrieval For The Prototype

**Rationale**: Integreat pages already provide useful metadata such as title,
content, language, hierarchy, URL, and update timestamps. The dataset is small
and clean (a few hundred well-structured pages from one API), so a custom
retrieval layer is roughly the same setup cost as standing up a turnkey stack
while preserving fine-grained control over chunk metadata — page path, parent
chapter, `last_updated`, language, source URL — which is exactly what powers
citations and journey grounding. Concretely: chunk by page/heading (the API
already returns topic-sized chunks), embed, store in a vector DB (Chroma,
LanceDB, or pgvector), top-k retrieval, optional rerank.

**Alternatives considered**:

- **Onyx/external document Q&A stack**: Self-hostable, but optimized for search
  rather than journey orchestration and fine-grained metadata control. It could
  only ever be the retrieval layer; the journey state machine, slot-filling, and
  option-chip flow are built on top regardless.
- **Manual source links only**: Safe for a demo, but does not generalize across
  journeys or languages.

## Decision: Use A Multilingual Embedding Model And Test Non-English First

**Rationale**: This is a ~20-language product, and Integreat exposes parallel
page IDs per language. A multilingual embedding model (e.g. BGE-m3 or
multilingual-e5 — both open and self-hostable) lets a query in Arabic, Farsi,
Ukrainian, etc. retrieve the right page even when the indexed content is German,
after which the answer is rendered in the user's language. The non-English
retrieval path MUST be tested on day one, not late in the build, because it is
the primary path for the target users — not an edge case.

**Alternatives considered**:

- **English/German-only embeddings with translate-then-search**: Adds a
  translation hop, more latency, and a failure point on the most-used path.
- **Defer multilingual testing to the end**: High risk; a broken non-English
  path discovered late invalidates the core value proposition.

## Decision: Treat Stage Helpers As Bounded Agents Or Tools

**Rationale**: Helpers such as housing, registration, documents, appointments,
translation, follow-up, and handoff should feel agentic to the user, but they
must remain bounded by journey graph state, source retrieval, and privacy rules.

**Alternatives considered**:

- **One monolithic assistant prompt**: Simpler, but harder to test and harder to
  explain as a safe system.
- **Fully autonomous multi-agent system**: Impressive, but too risky and too
  broad for the hackathon.

## Decision: Store Sensitive Context Locally Or Session-Only By Default

**Rationale**: The privacy goal is not just protecting data after collection;
it is avoiding unnecessary collection. City, language, journey state, and
document checklist progress can often stay on-device or in session state.

**Alternatives considered**:

- **Server-side profile**: Easier for cross-device continuity, but increases
  trust and compliance burden.
- **No memory at all**: Private, but forces users to repeat themselves and hurts
  the handholding experience.

## Decision: Keep TEE/Confidential Compute As An Optional Hardening Path

**Rationale**: If stronger external/cloud-hosted models are needed for sensitive
reasoning, confidential processing can reduce exposure. It should not replace
minimization, self-hosting, source grounding, or consent.

**Alternatives considered**:

- **TEE-first architecture**: Strong privacy story, but complex and not
  necessary for every prototype path.
- **External model calls with raw data**: Better model quality, but conflicts
  with the core privacy promise.

## Decision: Use Editable Human Handoff Summaries

**Rationale**: The system should support counselors without forwarding raw chat
logs. A user-reviewed summary is safer, clearer, and easier to consent to.

**Alternatives considered**:

- **Raw transcript handoff**: Maximum context, but privacy-invasive.
- **No handoff**: Unsafe for urgent, unclear, or high-risk cases.
