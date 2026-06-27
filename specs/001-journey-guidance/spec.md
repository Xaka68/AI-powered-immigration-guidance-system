# Feature Specification: Journey-Based Immigration Guidance System

**Feature Branch**: `main`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Build a generalizable immigration guidance system with dynamic chatbot and agentic helpers. The Munich arrival, housing, apartment registration, and document-preparation path is the first story, but the product must support many migrant journeys."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route A New Arrival Into A Guided Journey (Priority: P1)

A newly arrived migrant asks a broad question such as "I just came to Germany.
What should I do now?" The system orients the user, detects likely needs, and
offers clear next-step choices such as housing, address registration, health,
German course, school, work, or human counseling. The user can choose a path
without needing to know German bureaucracy terms.

**Why this priority**: This is the core product promise. The system must turn
an overwhelming open question into an actionable, safe, source-grounded journey.

**Independent Test**: A user enters the broad arrival question and receives
stage options, a privacy explanation, and a recommended first journey without
the assistant inventing legal or bureaucratic steps.

**Acceptance Scenarios**:

1. **Given** a user asks "I just came to Germany. What should I do now?", **When**
   the system responds, **Then** it presents options-first journey choices and
   asks at most one necessary clarification before routing.
2. **Given** a user selects housing and registration, **When** the journey
   starts, **Then** the system shows a structured path with trusted sources,
   freshness information when available, and next actions.

---

### User Story 2 - Complete The Munich Housing And Registration Demo Slice (Priority: P1)

A migrant in Munich needs help finding housing and understanding what to do
after getting an apartment. The system guides them through home-finding
resources, address registration, required documents, edge cases, and safe
handoff. It can help prepare a checklist or draft document support while
explaining why any personal data is needed.

**Why this priority**: This is the first polished vertical demo. It proves that
the general journey model can handle a real, emotionally meaningful, multi-step
case.

**Independent Test**: A user selects Munich housing/address registration and
receives a sourced action plan covering housing resources, registration steps,
documents to prepare, edge cases, and human handoff triggers.

**Acceptance Scenarios**:

1. **Given** a user has found an apartment in Munich, **When** they ask what to
   do next, **Then** the system explains registration-related steps using
   current trusted sources and asks only for necessary context.
2. **Given** the user is missing a landlord confirmation or appointment, **When**
   they indicate that edge case, **Then** the system explains the safe next
   action, uncertainty, and escalation path without inventing procedures.
3. **Given** the user wants help filling a form or checklist, **When** personal
   data is requested, **Then** the system explains the purpose, keeps the data
   local/session-only by default, and lets the user review the output before
   using or sharing it.

---

### User Story 3 - Use Stage-Specific Helpers Across Many Journeys (Priority: P2)

A user with another need, such as German courses, school enrollment, health
insurance, work, urgent housing, or human counseling, can be routed to the same
shared stage model. Helpers support orientation, eligibility/context, action
planning, documents, appointments, communication, follow-up, and handoff.

**Why this priority**: The product must be generalizable beyond the Munich
housing demo while still preserving authored journeys and source grounding.

**Independent Test**: A second journey can reuse the same helper stages and
privacy/source rules without requiring a new chatbot architecture.

**Acceptance Scenarios**:

1. **Given** a user asks for German course help, **When** the system routes the
   request, **Then** it uses the same stages and source-grounding rules as the
   housing journey.
2. **Given** a user asks two things at once, such as housing and German course,
   **When** the system responds, **Then** it splits the needs and asks the user
   which journey to handle first.

---

### User Story 4 - Escalate Safely To Human Counseling (Priority: P2)

A user can request a human counselor, or the system can recommend escalation
when sources are missing, conflicting, stale, legally sensitive, emotionally
high-risk, or urgent. The system prepares a concise summary that the user can
edit and approve before sharing.

**Why this priority**: The assistant must support human counselors and avoid
over-answering risky cases.

**Independent Test**: A risky or unclear case produces an editable handoff
summary and no raw chat transcript is shared by default.

**Acceptance Scenarios**:

1. **Given** a user describes an urgent or legally unclear issue, **When** the
   system detects risk, **Then** it recommends human counseling and explains why.
2. **Given** the user agrees to handoff, **When** the summary is prepared,
   **Then** the user can edit and approve it before anything is shared.

### Edge Cases

- User asks a broad question with no city, language preference, or concrete
  topic.
- User mixes languages or uses informal/non-German bureaucracy terms.
- User asks multiple unrelated questions in one message.
- Trusted sources are missing, stale, conflicting, or do not cover the edge
  case.
- User needs urgent help, has no stable housing, or is in temporary
  accommodation.
- User is missing a required document, cannot access an appointment, or cannot
  communicate in German.
- User wants document/form help that requires personal data.
- User declines storage, handoff, or the use of sensitive personal context.

### Journey, Sources, And Privacy *(mandatory)*

**User Stage**: orientation, eligibility-context, action plan, documents,
appointment-contact, translation-communication, follow-up, human handoff

**Journey Type**: authored journey graph for multi-step flows; one-shot Q&A for
simple source-grounded answers; human handoff for risky or unsupported cases

**Canonical Story Fit**: arrival-to-Germany, home finding, address registration,
document preparation, communication support, follow-up

**Trusted Sources**: Integreat pages, official municipal pages, official forms,
local counseling resources, BAMF or other official public-information sources
when relevant

**Freshness Display**: Answers show source title, link, and `last_updated` or
equivalent freshness metadata when available. If freshness is unavailable, the
answer must say that the date could not be verified.

**Personal Data Requested**: The system may ask for city, preferred language,
selected journey, current stage, and only the minimal case details needed for
the active step. Document preparation may request form fields, but only after
explaining why they are needed and how they will be handled.

**Privacy Controls**: Session-only mode by default for sensitive facts, optional
local wallet for reusable context, redaction/minimization before model use,
consent screen before human handoff, and confidential processing/TEE path for
sensitive server-side reasoning when applicable.

**Options-First States**: Journey choices, city/language selection, current
housing situation, document status, appointment status, edge-case selection,
human handoff consent, and next-step checklists should be presented as
structured options before free text.

**Human Handoff Rule**: Escalate when the user requests a human, when the case
is urgent or emotionally high-risk, when legal/source uncertainty is high, when
the user lacks required documents and sources do not cover the edge case, or
when the next step requires individualized professional judgment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route broad migrant questions into one or more known
  journey categories.
- **FR-002**: System MUST support authored journey graphs with stages, steps,
  branch conditions, source bindings, and escalation exits.
- **FR-003**: System MUST provide stage-specific helpers for orientation,
  eligibility/context, action plan, documents, appointment/contact,
  translation/communication, follow-up, and human handoff.
- **FR-004**: System MUST present structured options before free-text input
  whenever the next branch is known.
- **FR-005**: System MUST support the Munich arrival-to-housing-to-address
  registration demo as the first end-to-end journey.
- **FR-006**: System MUST cite trusted sources for material procedural, legal,
  or local-service claims.
- **FR-007**: System MUST show source freshness metadata when available and
  state when freshness cannot be verified.
- **FR-008**: System MUST ask only for personal data needed for the current
  stage and explain why it is needed.
- **FR-009**: System MUST store sensitive personal context locally or
  session-only by default unless the user explicitly consents otherwise.
- **FR-010**: System MUST support document/checklist preparation with user
  review before download, use, or sharing.
- **FR-011**: System MUST provide an escalation path when source coverage,
  urgency, emotional sensitivity, or legal uncertainty makes an automated
  answer unsafe.
- **FR-012**: System MUST allow the user to review and edit any handoff summary
  before it is shared with a human counselor.
- **FR-013**: System MUST avoid sharing raw chat transcripts by default.
- **FR-014**: System MUST expose which personal fields were used, stored, and
  shared for a given answer or handoff.
- **FR-015**: System MUST handle multi-intent questions by splitting needs and
  asking the user which journey to handle first.

### Key Entities *(include if feature involves data)*

- **Journey**: A trusted, authored flow for a migrant need, such as arrival,
  housing, registration, German courses, school, health, work, or counseling.
- **Stage**: A reusable part of a journey, such as orientation, context,
  documents, appointment, communication, follow-up, or handoff.
- **Step**: A specific action or information unit inside a stage, with source
  bindings, branch conditions, and possible next actions.
- **User Context**: Minimal user-provided facts needed for the current step,
  such as city, preferred language, housing situation, appointment status, or
  document status.
- **Source Reference**: Trusted source metadata including title, URL,
  language, topic, source type, and freshness date when available.
- **Helper**: A bounded stage-specific assistant, subagent, tool, or workflow
  that performs one kind of support while obeying the constitution.
- **Document Draft**: A user-reviewed form, checklist, message, or script
  generated from explicit user-provided fields and trusted source constraints.
- **Handoff Summary**: A concise counselor-facing summary that the user reviews
  and approves before sharing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A broad "I just came to Germany" question can be routed into a
  journey choice in under two assistant turns.
- **SC-002**: The Munich arrival/housing/registration demo produces a complete
  source-grounded action plan with next steps, documents, edge cases, and
  handoff option.
- **SC-003**: 100% of material procedural or local-service claims in the demo
  answer include a trusted source reference.
- **SC-004**: The primary demo asks for no unnecessary sensitive personal data
  before giving useful next steps.
- **SC-005**: The user can identify what data was used, stored, and shared for
  the current answer or handoff.
- **SC-006**: A risky or unsupported edge case triggers uncertainty or human
  handoff instead of an unsupported automated answer.
- **SC-007**: A second journey can reuse the same stage/helper model without
  changing the product concept.

## Assumptions

- The MVP will prove the general system through one polished Munich-focused
  arrival/housing/registration journey.
- Integreat content is a resource directory ("sign post"), not a process engine:
  it describes offices, courses, and services but does not encode the ordered
  steps, prerequisites, and branches of a journey. Journey skeletons are
  therefore hand-authored, and the content layer grounds what each step says.
  That the chosen journey's procedure is reconstructable from available content
  must be verified in the first hours of the build.
- Integreat and official public sources provide enough content to ground the
  first demo journey; missing content will trigger uncertainty or handoff.
- Users may have limited German proficiency and may prefer non-German answers;
  retrieval uses a multilingual embedding model so a non-German query can match
  German-language source pages, and the non-German path is validated early.
- The prototype may use fast development tooling, but the product narrative
  remains self-hostable, source-grounded, privacy-minimizing, and compatible
  with confidential processing.
- Human handoff can be demonstrated through an editable summary even if a live
  counseling backend is not integrated in the first demo.
