# Architecture: Journey-Based Immigration Guidance System

## Product Shape

The product is a guided immigration companion for migrants and refugees. It
looks conversational, but the core behavior is not a free-form chatbot. It is a
journey system:

```text
User asks for help
-> system routes the need
-> authored journey graph controls trusted steps
-> stage helpers support the current step
-> retrieval grounds claims in sources
-> privacy layer minimizes data use
-> user gets next steps, documents, sources, and handoff option
```

The main idea is:

> Agents make the help feel personal. Journey graphs keep it safe. Sources keep
> it trustworthy. Privacy controls keep user context under control.

## Generalizable System

The product should support many journeys, including:

- first steps after arrival
- housing and address registration
- German courses
- school and childcare
- health insurance and medical help
- work and Ausbildung
- urgent housing or crisis support
- human counseling handoff

Each journey uses the same stage model:

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

## MVP Demo Slice

The first polished journey is:

```text
New arrival in Munich
-> needs housing or has found an apartment
-> needs address registration guidance
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

## Core Components

### Journey Router

Detects the user's likely need and routes to one or more journeys.

Examples:

- "I just came to Germany" -> arrival journey
- "I found an apartment" -> address registration journey
- "I need Kita and German course" -> split into childcare and German course

### Authored Journey Graph Engine

Stores trusted steps, branch conditions, and escalation exits.

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

These can later be implemented as subagents, tools, workflows, or MUTagent-style
workers. The important part is that each helper has strict boundaries.

### Source/RAG Layer

Retrieves trusted content from:

- Integreat pages
- official municipal pages
- official forms
- local counseling resources
- other official public sources when relevant

Every material procedural claim should point back to a source.

### Privacy Layer

Controls what data is requested, used, stored, and shared.

Default behavior:

- ask only for data needed for the current step
- store sensitive facts session-only unless the user opts in
- keep reusable context in a local wallet when possible
- redact or minimize before model use
- show a privacy receipt
- require consent before human handoff

Optional future hardening:

- self-hosted models
- confidential processing
- TEE-backed sensitive reasoning path

### Human Handoff Layer

Used when the user asks for a counselor or the system detects risk,
uncertainty, urgency, or missing source coverage.

The user sees and edits the summary before sharing. Raw chat is not forwarded by
default.

## Data Flow

```text
1. User sends message or chooses an option.
2. Router identifies likely journey and stage.
3. Privacy layer checks what context is needed.
4. System asks at most one necessary clarification.
5. Journey graph selects trusted next step.
6. Source layer retrieves relevant pages and metadata.
7. Stage helper prepares answer/action/document/handoff.
8. Verification checks material claims against sources.
9. UI shows structured answer, sources, options, and privacy receipt.
10. Journey state stays local/session-only by default.
```

## Safety Boundaries

- The assistant does not provide legal advice.
- The assistant provides legal and municipal information navigation.
- It does not invent procedures, deadlines, requirements, or documents.
- It flags missing, stale, or conflicting information.
- It escalates risky cases to human counselors.
- It does not forward raw chat by default.

## Next Build Target

Build the first working slice:

```text
Arrival question
-> route to housing/address registration
-> show options-first path
-> retrieve/source Munich registration information
-> generate action plan and document checklist
-> show privacy receipt
-> offer editable human handoff summary
```
