# Project Documents

Start here if you are joining the project or preparing the pitch.

## Core Documents

- [Constitution](../.specify/memory/constitution.md): Product principles and non-negotiable
  safety/privacy rules.
- [Architecture](./architecture.md): Readable system architecture and MVP slice.
- [Product Spec](../specs/001-journey-guidance/spec.md): Generalizable product
  requirements.
- [Implementation Plan](../specs/001-journey-guidance/plan.md): Technical plan
  and architecture decisions.
- [Research Decisions](../specs/001-journey-guidance/research.md): Why we chose
  journey graphs, options-first UX, custom retrieval, and privacy defaults.
- [Data Model](../specs/001-journey-guidance/data-model.md): Core entities for
  journeys, helpers, sources, wallet context, documents, and handoff.
- [Journey Contract](../specs/001-journey-guidance/contracts/journey-contract.md):
  Shared interface shape for UI, journey engine, helpers, retrieval, and handoff.
- [Quickstart Validation](../specs/001-journey-guidance/quickstart.md): Demo and
  test script for the MVP journey.

## Product Summary

We are building a journey-based immigration guidance system, not a generic
chatbot. It routes migrant questions into trusted journeys and uses
stage-specific helpers for housing, registration, documents, appointments,
communication, follow-up, and human counseling.

The first MVP journey is:

```text
New arrival in Munich
-> housing/home finding
-> address registration
-> document/checklist preparation
-> edge-case support
-> consent-based human handoff
```

The architecture should generalize to many other migrant journeys.
