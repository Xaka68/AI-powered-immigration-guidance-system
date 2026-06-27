# Integreat Compass

AI-powered immigration guidance for migrants and refugees in Germany.
Built for the AI4Good Hackathon, June 27-28 2026.

## What it does

Routes migrant questions into source-grounded, stage-specific journeys using
Integreat content. Asks at most one clarification question. Returns a structured
action plan with next steps, documents, sources, and a human handoff option.

## Repo layout

```
backend/     Python/FastAPI — RAG pipeline, intent splitter, answer generator
frontend/    Next.js — chat UI, options-first flow, structured answer display
data/        Journey graphs, cached Integreat sources, evaluation fixtures
docs/        Architecture, constitution, product spec references
specs/       Detailed feature spec, plan, data model, contracts
```

## Core docs

- [Constitution](.specify/memory/constitution.md) — non-negotiable product principles
- [Architecture](docs/architecture.md) — system design and MVP slice
- [Spec](specs/001-journey-guidance/spec.md) — full product requirements
- [Plan](specs/001-journey-guidance/plan.md) — implementation plan

## Demo scenario

> "I am in Munich. I need Kita Anmeldung and Deutschkurs. Please answer in Arabic."

Expected: splits into two intents, asks one clarification (child's age), returns
structured action plan in Arabic with Munich Integreat sources.

## Data source

Integreat CMS API — Munich test content:
`https://cms.integreat-app.de/testumgebung-frag-integreat/de/wp-json/extensions/v3/pages/`
