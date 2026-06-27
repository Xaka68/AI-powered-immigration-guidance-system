# Implementation Plan: Journey-Based Immigration Guidance System

**Branch**: `main` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-journey-guidance/spec.md`

## Summary

Build a generalizable guidance system that routes migrant questions into trusted
journeys, then uses stage-specific helpers to provide orientation, context
questions, action plans, document support, appointment/contact guidance,
translation/communication help, follow-up, and human handoff. The first MVP
slice proves the model through a Munich arrival, housing, address registration,
and document-preparation journey.

The architecture separates:

1. **Authored journey graph** for trusted steps and branch conditions.
2. **Conversation and helper orchestration** for dynamic routing and user
   support.
3. **Source-grounded retrieval** for Integreat and official/local information.
4. **Privacy controls** for local wallet, session-only data, redaction, consent,
   and optional confidential processing.

## Technical Context

**Language/Version**: TypeScript/React for the prototype frontend; Python 3.12+
for backend/RAG services if a separate backend is built.

**Primary Dependencies**: React or Next.js-style web UI, FastAPI-style service
boundary if needed, lightweight vector or keyword retrieval, Integreat CMS API,
official source ingestion, optional MUTagent-style orchestration for helper
agents, optional AWS confidential-compute proof path.

**Storage**: Local browser storage or IndexedDB for user wallet/session state;
repository-authored JSON/YAML journey graphs; lightweight local/vector index for
retrieved source metadata; no server-side sensitive profile persistence by
default.

**Testing**: Scenario-based validation for the canonical Munich journey,
source-grounding checks, privacy-minimization checks, and handoff-summary checks.

**Target Platform**: Web prototype usable on laptop and mobile browser.

**Project Type**: Web application with reusable journey configuration and
optional backend/RAG service.

**Performance Goals**: Primary demo path should respond quickly enough for live
judging; source retrieval should return usable citations within one interaction
cycle.

**Constraints**: LLM must not invent procedure steps; sensitive user data must
be minimized; all material procedural claims need sources; human handoff must be
consent-based; MVP must remain buildable during the hackathon.

**Scale/Scope**: General architecture for many migrant journeys; first
implemented vertical is Munich arrival -> home finding -> address registration
-> document preparation -> handoff.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Human-centered stage**: PASS. The product is organized by user stages:
  orientation, eligibility/context, action plan, documents, appointment/contact,
  communication, follow-up, and human handoff.
- **Authored journey boundary**: PASS. Multi-step flows are represented by
  authored journey graphs. Helpers may route and explain, but cannot invent
  official steps.
- **Source grounding**: PASS. The retrieval layer must attach source title, URL,
  source type, language, and freshness metadata where available.
- **Privacy minimization**: PASS. Session-only handling is default for sensitive
  facts; local wallet is optional; redaction and consent are explicit boundaries.
- **Options-first UX**: PASS. The primary interaction model uses chips,
  checklists, and structured choices before free text.
- **Human handoff**: PASS. Handoff requires editable user-approved summary and
  never forwards raw chat by default.
- **Independent validation**: PASS. The Munich arrival/housing/registration path
  provides a demo and validation scenario.

## Project Structure

### Documentation (this feature)

```text
specs/001-journey-guidance/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── journey-contract.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   ├── journeys/
│   ├── wallet/
│   └── services/
└── tests/

backend/
├── src/
│   ├── api/
│   ├── retrieval/
│   ├── orchestration/
│   └── privacy/
└── tests/

data/
├── journeys/
├── sources/
└── eval/

docs/
├── README.md
├── constitution.md
└── architecture.md
```

**Structure Decision**: Use a web-app layout with optional backend services and
data-driven journey configuration. The frontend can demonstrate the full guided
experience even if the backend/RAG layer is initially mocked or local. Journey
graphs and evaluation fixtures live under `data/` so new migrant journeys can be
added without rewriting the core app.

## Architecture

```text
User
  -> Chat/Journey UI
  -> Journey Router
  -> Authored Journey Graph Engine
  -> Stage Helper Orchestrator
       -> Source/RAG Helper
       -> Document Helper
       -> Communication Helper
       -> Follow-Up Helper
       -> Handoff Helper
  -> Privacy Boundary
       -> local/session wallet
       -> redaction/minimization
       -> optional TEE/confidential path
  -> Source-Grounded Response + Privacy Receipt
```

### Core Components

- **Journey Router**: Classifies the user's broad or multi-intent question into
  one or more known journey categories.
- **Journey Graph Engine**: Loads authored steps, branch conditions, source
  requirements, required context fields, and escalation exits.
- **Stage Helper Orchestrator**: Calls bounded helpers for the active stage.
  Helpers may be implemented as functions, subagents, tools, or MUTagent-style
  workers, but must obey the constitution.
- **Source/RAG Layer**: Retrieves Integreat and official/local pages, preserving
  title, URL, language, topic, and freshness metadata.
- **Privacy Wallet**: Stores only user-approved local/session context and exposes
  what was used, stored, or shared.
- **Document Preparation Layer**: Produces user-reviewed checklists, form drafts,
  or message drafts from explicit user-provided fields.
- **Human Handoff Layer**: Creates editable summaries and blocks sharing until
  the user consents.
- **Confidential Processing Layer**: Optional path for sensitive reasoning with
  self-hosted or confidential infrastructure.

## Phase 0: Research

See [research.md](./research.md).

## Phase 1: Design

See [data-model.md](./data-model.md), [contracts/journey-contract.md](./contracts/journey-contract.md),
and [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- **Human-centered stage**: PASS. Data model has explicit `Stage` and
  `StageHelper` entities.
- **Authored journey boundary**: PASS. `JourneyGraph` owns procedure steps;
  helper outputs are bounded by graph state.
- **Source grounding**: PASS. `SourceReference` is required for material claims.
- **Privacy minimization**: PASS. `PrivacyReceipt` and `UserContextField`
  model why data is needed, storage, and sharing status.
- **Options-first UX**: PASS. `OptionSet` is a first-class entity for branch
  decisions.
- **Human handoff**: PASS. `HandoffSummary` requires user review and consent.
- **Independent validation**: PASS. Quickstart defines the Munich demo and edge
  case validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
