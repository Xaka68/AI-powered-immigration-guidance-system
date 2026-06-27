<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles:
- I. Human-Centered Stage Guidance: unchanged
- II. Authored Journeys, Not Invented Procedures: unchanged
- III. Source-Grounded Legal Information: unchanged
- IV. Privacy By Minimization And User Control: unchanged
- V. Safe Escalation To Human Counselors: unchanged
Added sections:
- Canonical Product Story
Removed sections:
- None
Templates requiring updates:
- .specify/templates/plan-template.md: updated
- .specify/templates/spec-template.md: updated
- .specify/templates/tasks-template.md: updated
- .specify/templates/checklist-template.md: reviewed, no constitution-specific change required
- AGENTS.md: updated
Follow-up TODOs:
- None
-->
# Confidential Journey Counselor Constitution

## Core Principles

### I. Human-Centered Stage Guidance

The product MUST guide migrants and refugees through concrete stages of a help
journey: orientation, eligibility/context, action plan, documents, appointment
or contact, translation/communication, follow-up, and human handoff. Features
MUST be designed around what a vulnerable user needs to do next, not around a
generic chatbot interaction. The default interaction MUST prefer simple options,
chips, and checklists over open-ended input whenever the next branch is known.

Rationale: users may face language, stress, literacy, and trust barriers.
Options-first guidance reduces confusion and constrains unsafe model behavior.

### II. Authored Journeys, Not Invented Procedures

The system MUST NOT allow an LLM to invent bureaucratic procedures, eligibility
rules, document requirements, deadlines, or official steps. Multi-step journeys
MUST be represented as authored journey graphs or explicit state machines with
known steps, branch conditions, and escalation exits. The LLM may classify
intent, ask clarifying questions, fill slots, translate, summarize, and explain
retrieved content, but it MUST navigate trusted structures rather than create
new procedure logic.

Rationale: a hallucinated step can cause real harm. Accuracy lives in curated
journey structure; dynamism lives in routing, language, and personalization.

### III. Source-Grounded Legal Information

Every user-facing claim about legal, municipal, medical, school, childcare,
housing, benefits, or immigration-related processes MUST be grounded in
retrieved trusted sources. Answers MUST include source titles, links, and
freshness metadata when available, such as `last_updated`. The assistant MUST
distinguish legal information navigation from legal advice, state uncertainty
when sources are incomplete or outdated, and escalate risky cases to human
counseling.

Rationale: the product supports counseling; it does not replace qualified legal
or social-service professionals.

### IV. Privacy By Minimization And User Control

The system MUST ask for, store, and transmit only the personal context needed
for the current step. Reusable user context SHOULD live on the user's device
or in a local personal data wallet. Server-side processing MUST be stateless
with respect to sensitive profile data unless the user explicitly consents to
retention. Sensitive facts MUST be redacted or generalized before model calls
when full detail is not required. Confidential processing, including TEEs, MAY
be used when stronger external or cloud-hosted AI is needed, but only if
sensitive data remains protected within the confidential boundary or is
minimized before leaving it.

Rationale: the strongest privacy guarantee is avoiding unnecessary collection;
confidential compute is a hardening layer, not permission to over-collect.

### V. Safe Escalation To Human Counselors

The system MUST provide a clear path to human counseling when a case is urgent,
high-risk, legally uncertain, emotionally sensitive, or outside retrieved
source coverage. Human handoff MUST be consent-based: the user MUST see,
edit, and approve the summary before it is shared. Raw chat transcripts MUST
NOT be forwarded by default. Handoff summaries MUST contain only the minimum
context needed for a counselor to help.

Rationale: responsible AI counseling means knowing when not to answer and
making escalation safe, transparent, and useful.

## Canonical Product Story

The reference product story is a newly arrived immigrant in Munich who asks:
"I just came to Germany. What should I do now?"

The expected experience is a guided journey, not a single generic answer. The
assistant SHOULD orient the user, identify the user's immediate goal, and route
them into stage-specific helpers such as:

- Home finding: explain trusted housing resources, search strategies, warnings,
  and when to seek human support.
- Address registration: explain that Munich residents may need to register
  their apartment with the city and prepare official registration materials,
  with all details verified against current official sources.
- Document preparation: help the user understand, collect, translate, and
  prepare forms or checklists, such as landlord confirmation and city
  registration forms when verified as required by current sources.
- Edge-case handling: handle cases such as no permanent apartment yet,
  temporary accommodation, missing landlord confirmation, language barriers,
  no appointment availability, unclear legal status, or urgent risk.
- Communication support: draft plain-language German messages, appointment
  questions, or office scripts while showing the user's original language.
- Follow-up: track what the user has completed, what remains, and what must be
  confirmed with official offices or human counselors.

Stage-specific helpers MAY be implemented as subagents, tools, modules, or
prompted workflows, but each helper MUST obey the same boundaries: no invented
procedure steps, source-grounded claims, options-first interaction, minimum
personal data, and consent before sharing with a human. When document creation
requires personal data, the product MUST explain why the data is needed, prefer
local/session-only handling, and allow the user to review the generated form
before using or sharing it.

## AI And Data Boundaries

The product MUST treat AI components as bounded assistants with explicit
responsibilities:

- Intake/routing may detect language, region, urgency, topic, and likely
  journey, but MUST NOT infer sensitive identity attributes unless needed.
- Clarification logic MUST ask at most one necessary question before answering
  or progressing, unless the user explicitly chooses a deeper guided journey.
- Retrieval MUST prioritize Integreat content and official/local sources.
- Answer generation MUST produce structured next steps with citations and
  uncertainty, not free-form legal advice.
- Verification MUST check source support for material claims before display.
- Logging MUST avoid raw sensitive messages, personal identifiers, and full
  transcripts. Operational logs SHOULD use aggregate categories and error
  codes.
- Model providers, cloud services, and external agents MUST be swappable and
  documented. Any non-self-hosted or non-confidential processing path MUST be
  visible in the plan and demo narrative.

## Delivery Workflow And Quality Gates

Every feature spec and implementation plan MUST pass these gates:

1. Identify the user stage and journey being served.
2. State whether the flow uses an authored journey graph, one-shot Q&A, or
   human handoff.
3. List the trusted sources used and how freshness is shown.
4. List the personal data requested, where it is stored, and why each field is
   necessary.
5. Define the option-first UI states and free-text fallback behavior.
6. Define at least one independent test or demo scenario with expected sources,
   expected next steps, and privacy expectations.
7. Define escalation behavior for missing, stale, conflicting, or risky source
   information.

Implementation MUST prioritize one polished, end-to-end journey before broad
generic coverage. New abstractions, agents, or confidential-compute components
MUST be justified by user value, privacy value, or source-grounding value.

## Governance

This constitution supersedes other project practices when there is conflict.
Changes require documenting the motivation, affected principles, migration
impact, and version bump in the Sync Impact Report.

Versioning follows semantic versioning:

- MAJOR: removal or incompatible redefinition of a core principle.
- MINOR: new principle, new mandatory quality gate, or materially expanded
  governance requirement.
- PATCH: wording clarification, typo fix, or non-semantic refinement.

All specs, plans, task lists, prototypes, and demos MUST be reviewed against
the Core Principles and Delivery Workflow gates. Any intentional violation MUST
be documented in the implementation plan's Complexity Tracking section with the
simpler alternative and reason for rejection.

**Version**: 1.1.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
