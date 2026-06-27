# Research: Journey-Based Immigration Guidance System

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
content, language, hierarchy, URL, and update timestamps. A custom retrieval
layer lets the team preserve this metadata for citations and freshness display.

**Alternatives considered**:

- **Onyx/external document Q&A stack**: Self-hostable, but optimized for search
  rather than journey orchestration and fine-grained metadata control.
- **Manual source links only**: Safe for a demo, but does not generalize across
  journeys or languages.

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
