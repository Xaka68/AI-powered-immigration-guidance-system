# Architecture: Journey-Based Immigration Guidance System

## Product Shape

The product is a guided immigration companion for migrants and refugees. It
looks conversational, but the core behavior is not a free-form chatbot. It is a
journey system:

```text
User asks for help
-> system routes the need
-> authored journey graph controls trusted steps
-> conversation personalizes and navigates the graph
-> retrieval grounds every claim in sources
-> privacy layer minimizes data use
-> user gets next steps, documents, sources, and handoff option
```

The main idea is:

> Conversation makes the help feel dynamic. Authored journey graphs keep it
> safe. Sources keep it trustworthy. Privacy controls keep user context under
> control.

## The Core Reframe: Three Separated Layers

Most "AI journey" designs mush three concerns together and then have to trade
accuracy against dynamism. This system keeps them apart on purpose. The two
judging criteria — "dynamic / journey-like" and "very high accuracy" for a
vulnerable population — are in tension only if the model is allowed to invent
bureaucracy. Separating these layers resolves that tension.

1. **Journey graph (authored, trustworthy).** A small set of hand-built journey
   templates expressed as explicit step-graphs / state machines. We curate the
   skeleton: the ordered steps, prerequisites, branch conditions, and escalation
   exits. **Accuracy lives here**, because the procedure is never left to the
   model.

2. **Routing & conversation (LLM, dynamic).** This is the part that feels
   dynamic: detect intent, ask clarifying questions, slot-fill the user's
   situation, and decide which branch of the graph applies to this person. The
   model **never invents steps** — it only navigates the authored graph and
   personalizes language.

3. **Content (RAG, grounded).** Each step's actual text, links, and addresses
   are retrieved from source pages at render time, always with a citation to the
   source page and its `last_updated` date.

So **"dynamic" = the conversation and which path you take through a trusted
graph** — not "the LLM makes up the bureaucracy." That single distinction is
what lets the product score on both axes instead of trading one for the other.

## Source Data Reality (Integreat)

The architecture is grounded in what the Integreat API actually returns, not in
assumptions:

- A **flat list of pages**, each with a `parent.id`, so the content forms a
  **hierarchical tree** (chapters -> subpages).
- Clean, semantic **HTML content** per page, plus a short **excerpt**.
- A **`last_updated`** timestamp per page (powers freshness in citations).
- **`available_languages`** with **parallel page IDs across ~20 languages**
  (de, en, ar, fa, tr, uk, so, ckb, kmr, ...). This gives multilingual content,
  pre-chunked by topic, with a built-in taxonomy, essentially for free.

The one limitation to internalize before building:

> Integreat is a **"sign post," not a process engine**. The content *describes
> resources* (doctors, German courses, counseling offices). It does **not**
> natively encode the *procedure* of a bureaucratic journey — the ordered steps,
> prerequisites, documents, and decision branches.

**Consequence:** the journey skeletons in layer 1 must be **hand-authored**. The
content layer grounds *what each step says*; it does not supply *the steps
themselves*. Verifying that a chosen journey's procedure is reconstructable from
the available content is a first-hour task, not a discovery to make at hour 30.

## Options-First Interaction (an accuracy decision, not just UX)

At every decision point the default interaction is **tappable options
(chips/buttons)**, with free text as the fallback — not the primary input.

For users with low German or low literacy, structured choices win on every axis
at once:

- easier to use and fewer dead-ends (accessibility), and
- they constrain the model's branching to a **known set**, which directly buys
  accuracy and safety (hallucination control).

"Options-first" is therefore both the accessibility story and the
hallucination-control story in a single move. Free-text intent is supported, but
it is funneled back into the authored option set.

## Runtime Loop

```text
User message
-> intent classifier: which journey? or one-shot Q&A?
-> if journey: slot-check (do I know the facts this branch needs:
      city, status, has-children, ...?)
   -> if a slot is missing: present 2-4 tappable options (not open-ended)
-> once slots are filled: advance the journey state
-> retrieve grounded content for the current step
-> render: step + citation (source + last_updated) + next-action options
-> loop until the goal is reached or a defined escalation exit fires
```

Journey state (where the user is, what they have told us) lives **on the
device**, not the server — this is the "Personal Data Wallet" story. Each LLM
call is stateless with respect to personal data; only the minimum context
needed for the current turn is passed.

## Generalizable System

The product is designed to support many journeys using one stage model, even
though the hackathon scope nails only one (see MVP slice):

- first steps after arrival
- housing and address registration
- German courses
- school and childcare
- health insurance and medical help
- work and Ausbildung
- urgent housing or crisis support
- human counseling handoff

Shared stage model for every journey:

```text
Orientation
-> eligibility/context
-> action plan
-> documents
-> appointment/contact
-> translation/communication
-> follow-up
-> human handoff
```

The generality is a design property of the graph engine — not something the LLM
generates on the fly. A generic "any journey, invented at runtime" engine is
explicitly out of scope (see Traps).

## MVP Demo Slice

The first polished journey is:

```text
New arrival in Munich
-> needs housing or has found an apartment
-> needs address registration guidance (Anmeldung)
-> needs documents/checklist support
-> may have edge cases
-> may need human help
```

This slice is strong because it shows:

- a broad user question becoming a guided journey
- housing and bureaucracy in one flow
- official source grounding
- document support
- privacy-sensitive personal data handling
- human counselor handoff

For the hackathon, **fake the generality and nail this one journey
end-to-end** — in the user's non-German language, with grounded content and the
option-chip UX. A polished single vertical demos far better than a broad,
shallow one.

## Core Components

### Journey Router

Detects the user's likely need and routes to one or more journeys. Routing is
LLM-driven but **gated to the known journey set** — it classifies into authored
journeys, it does not invent them.

Examples:

- "I just came to Germany" -> arrival journey
- "I found an apartment" -> address registration journey
- "I need Kita and German course" -> split into childcare and German course

### Authored Journey Graph Engine

Stores trusted steps, branch conditions, slot requirements, and escalation
exits. This is the accuracy backbone.

The model must not invent official steps. It only navigates the graph, explains
sources, asks clarifying questions, and personalizes language.

### Stage Helpers

Bounded helpers for specific user tasks:

- home finding helper
- registration helper
- document helper
- appointment/contact helper
- translation/communication helper
- follow-up helper
- human handoff helper
- source verification helper
- privacy review helper

These can later be implemented as subagents, tools, or workflows. The important
part is that each helper has strict boundaries.

### Source / RAG Layer

A **lightweight custom RAG**, not a turnkey search platform. The data is small
and already clean (a few hundred well-structured pages from one API), and we
need fine control over **chunk metadata** — page path, parent chapter,
`last_updated`, language, source URL — because that metadata is what powers
citations and journey grounding.

Pipeline:

```text
chunk by page/heading  (API already gives topic-sized chunks)
-> embed with a multilingual model
-> store in a vector DB (Chroma / LanceDB / pgvector)
-> top-k retrieval
-> optional rerank
```

Retrieval details that matter for this problem specifically:

- **Embed at page (or heading) level.** The API already returns topic-sized
  chunks, so a heavy chunker is unnecessary.
- **Use a multilingual embedding model** (e.g. BGE-m3 or multilingual-e5 — both
  open and self-hostable) so an Arabic query retrieves the right page even when
  the indexed content is German, then answer in the user's language. This is a
  ~20-language product: **test the non-English path on day one, not at hour 30.**

> On Onyx (ex-Danswer): self-hostable and ticks the open-source box, but it is
> built for doc Q&A/search. It can only ever be the retrieval layer — it does
> not provide the journey state machine, slot-filling, or option-chip flow, all
> of which we build on top regardless. Prefer custom RAG unless a teammate
> already knows Onyx cold.

Every material procedural claim must point back to a source.

### Privacy Layer

Controls what data is requested, used, stored, and shared.

Default behavior:

- ask only for data needed for the current step
- store sensitive facts session-only unless the user opts in
- keep reusable context in a **local wallet** (localStorage / IndexedDB for the
  prototype)
- redact or minimize before model use
- show a privacy receipt
- require consent before human handoff

The LLM is stateless with respect to personal data; journey state is held
client-side and only minimal per-turn context is sent. For the demo this can be
simple, but it should be narrated loudly — it is the deck's title and a clear
stakeholder priority.

Optional future hardening:

- self-hosted models
- confidential processing
- TEE-backed sensitive reasoning path

### Human Handoff Layer

Used when the user asks for a counselor or the system detects risk, uncertainty,
urgency, or missing source coverage.

The user sees and edits the summary before sharing. Raw chat is not forwarded by
default.

## Mapping the Hard Constraints to Decisions

| Constraint | Decision |
| --- | --- |
| **Store data on end device / Personal Data Wallet** | Journey state and user-supplied facts stay client-side (localStorage/IndexedDB in the prototype). LLM calls are stateless w.r.t. personal data; pass only minimal per-turn context. |
| **Open source / open weights / self-hostable** | Design the model as **swappable**; demo on an open model (Qwen2.5, Llama 3.x, or Mistral-Small-24B). Embeddings are open (BGE-m3 / multilingual-e5) and self-hostable. |
| **Current legal situation taken into account** | Do not overpromise. Every claim carries a **citation + source `last_updated` date**; the model is **forbidden from asserting legal facts not in retrieved content**; and there is an explicit **"verify with the Beratungsstelle / talk to a human" exit**. Citations + freshness + human escalation *is* the accuracy story. |

## Data Flow

```text
1. User sends message or chooses an option.
2. Router classifies into a known journey (or one-shot Q&A) and stage.
3. Privacy layer checks what context is needed.
4. Slot-check; if a slot is missing, present 2-4 tappable options.
5. Journey graph selects the trusted next step.
6. Source layer retrieves relevant pages and metadata (multilingual).
7. Stage helper prepares answer/action/document/handoff.
8. Verification checks material claims against sources.
9. UI shows structured answer, sources (+ last_updated), options, privacy receipt.
10. Journey state stays local/session-only by default.
```

## Safety Boundaries

- The assistant does not provide legal advice.
- The assistant provides legal and municipal information navigation.
- It does not invent procedures, deadlines, requirements, or documents.
- It flags missing, stale, or conflicting information.
- It escalates risky cases to human counselors.
- It does not forward raw chat by default.

## Scope & Traps (~36h hackathon)

Nail one journey end-to-end. The agentic "any journey, generated on the fly"
dream is a multi-week build; fake the generality and ship one polished vertical.

Traps, in order of how likely they are to bite:

1. **Procedure not in the content.** Discovering at hour 30 that the journey's
   steps are not reconstructable from Integreat. Check this in the first two
   hours and **author the step skeleton deliberately**.
2. **Free-form branching.** Letting intent detection / branching go open-ended
   and watching accuracy collapse. **Gate it to the option set.**
3. **Scope creep** toward a generic journey engine.

## Next Build Target

Build the first working slice:

```text
Arrival question
-> route to housing/address registration
-> show options-first path
-> retrieve/source Munich registration information (multilingual)
-> generate action plan and document checklist
-> show privacy receipt (+ source last_updated)
-> offer editable human handoff summary
```
