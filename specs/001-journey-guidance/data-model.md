# Data Model: Journey-Based Immigration Guidance System

## Entity: Journey

Represents a trusted migrant guidance flow.

**Fields**:

- `id`: Stable identifier, such as `arrival_munich` or `german_course`.
- `title`: User-facing journey name.
- `description`: Short explanation of the journey.
- `region`: City/municipality scope when applicable.
- `languages`: Supported content/answer languages.
- `stages`: Ordered list of stage IDs.
- `entry_conditions`: Conditions for routing a user into this journey.
- `escalation_exits`: Conditions where the system should recommend human help.

**Relationships**:

- Contains many `Stage` entities.
- Uses many `SourceReference` entities.

## Entity: Stage

Represents a reusable part of a journey.

**Allowed stage types**:

- `orientation`
- `eligibility_context`
- `action_plan`
- `documents`
- `appointment_contact`
- `translation_communication`
- `follow_up`
- `human_handoff`

**Fields**:

- `id`: Stable identifier.
- `journey_id`: Parent journey.
- `type`: One of the allowed stage types.
- `goal`: What the user should accomplish in this stage.
- `required_context`: Minimal context fields needed before this stage can run.
- `option_sets`: Structured choices available to the user.
- `source_requirements`: Source categories needed to support this stage.
- `next_stage_rules`: Branching rules to advance the journey.

## Entity: Step

Represents one trusted action or information unit inside a stage.

**Fields**:

- `id`
- `stage_id`
- `title`
- `instruction`
- `required_sources`
- `required_context`
- `user_options`
- `edge_cases`
- `completion_criteria`

**Validation rules**:

- A procedural step must reference at least one `SourceReference`.
- A step that asks for personal data must reference a `UserContextField`.

## Entity: StageHelper

Represents a bounded helper, subagent, tool, or workflow for one stage.

**Fields**:

- `id`
- `type`: housing, registration, document, appointment, communication,
  follow-up, handoff, source retrieval, privacy review, or verification.
- `allowed_actions`: Actions the helper may perform.
- `forbidden_actions`: Actions the helper must not perform.
- `required_inputs`
- `outputs`
- `source_policy`
- `privacy_policy`

**Validation rules**:

- A helper may not create new official procedure steps.
- A helper output must identify whether it is source-grounded, user-provided,
  inferred, or uncertain.

## Entity: UserContextField

Represents one personal or situational field used in a journey.

**Fields**:

- `name`
- `purpose`
- `sensitivity`: low, medium, high.
- `required_for_step`
- `storage_location`: local wallet, session-only, server-temporary, or not
  stored.
- `retention`
- `shared_with_human`: yes/no/pending consent.

**Validation rules**:

- Every field must have a purpose.
- Sensitive fields default to session-only unless the user opts in.

## Entity: OptionSet

Represents structured choices shown before free text.

**Fields**:

- `id`
- `prompt`
- `options`: Labels and values.
- `free_text_fallback`: Whether free text is available.
- `privacy_note`: Optional explanation if the choice reveals sensitive context.

## Entity: SourceReference

Represents a trusted source used for retrieval and citations.

**Fields**:

- `id`
- `title`
- `url`
- `source_type`: Integreat, municipality, official form, counseling resource,
  BAMF, other official public source.
- `language`
- `region`
- `topic`
- `last_updated`
- `retrieved_at`
- `excerpt`

**Validation rules**:

- Material procedural claims must cite one or more source references.
- If freshness is missing, the answer must say the update date could not be
  verified.

## Entity: JourneyState

Represents the user's current progress.

**Fields**:

- `journey_id`
- `current_stage_id`
- `completed_steps`
- `pending_steps`
- `context_fields`
- `privacy_receipts`
- `handoff_status`

**Storage default**:

- Local or session-only unless the user explicitly opts into persistence.

## Entity: DocumentDraft

Represents a generated checklist, message, script, or form-support draft.

**Fields**:

- `id`
- `type`: checklist, message, office script, form support, counselor summary.
- `source_step_id`
- `input_fields`
- `generated_content`
- `review_status`
- `sharing_status`

**Validation rules**:

- The user must review before use or sharing.
- Generated form support must not claim official submission unless the user
  actually submits through an official channel.

## Entity: HandoffSummary

Represents a counselor-facing summary.

**Fields**:

- `id`
- `user_goal`
- `known_context`
- `sources_consulted`
- `completed_steps`
- `open_questions`
- `urgency`
- `user_edits`
- `consent_status`

**Validation rules**:

- Raw chat transcript is excluded by default.
- Sharing is blocked until consent is approved.

## Entity: PrivacyReceipt

Represents a user-visible privacy explanation for one answer or action.

**Fields**:

- `used_fields`
- `stored_fields`
- `shared_fields`
- `storage_locations`
- `retention`
- `confidential_processing_used`
- `human_shared`

**Validation rules**:

- A receipt should be shown after sensitive context use, document generation,
  or human handoff.
