# Contract: Journey Guidance Interfaces

This contract defines product-level interfaces between the UI, journey engine,
retrieval layer, helpers, privacy controls, and handoff flow. Exact API
transport may change during implementation.

## Start Or Continue A Journey

**Input**:

```json
{
  "message": "I just came to Germany. What should I do now?",
  "locale": "en",
  "region_hint": "munich",
  "journey_state": null,
  "wallet_context": {
    "preferred_language": "en",
    "city": "Munich"
  },
  "privacy_mode": "session_only"
}
```

**Output**:

```json
{
  "journey_id": "arrival_munich",
  "stage": "orientation",
  "assistant_message": "I can help you take this step by step.",
  "options": [
    {"id": "housing", "label": "Find a place to live"},
    {"id": "registration", "label": "Register my address"},
    {"id": "german_course", "label": "Find a German course"},
    {"id": "human", "label": "Talk to a counselor"}
  ],
  "next_action": "choose_option",
  "sources": [],
  "privacy_receipt": {
    "used_fields": ["preferred_language", "city"],
    "stored_fields": [],
    "shared_fields": [],
    "storage_locations": {"preferred_language": "local", "city": "local"},
    "retention": "session/local wallet",
    "confidential_processing_used": false,
    "human_shared": false
  }
}
```

## Render A Journey Step

**Input**:

```json
{
  "journey_id": "arrival_munich",
  "stage": "address_registration",
  "selected_option": "i_have_apartment",
  "context": {
    "city": "Munich",
    "housing_status": "has_apartment"
  }
}
```

**Output**:

```json
{
  "short_answer": "After moving into an apartment in Munich, prepare the official registration materials and follow the current city instructions.",
  "next_steps": [
    "Check the current official registration page.",
    "Prepare the required documents listed by the official source.",
    "If a landlord confirmation is required, request it from the landlord.",
    "Book or attend the registration appointment according to current city guidance."
  ],
  "documents_needed": [
    {
      "name": "Landlord confirmation",
      "source_id": "munich-registration-source",
      "status": "verify_current_requirement"
    },
    {
      "name": "Registration form",
      "source_id": "munich-registration-source",
      "status": "verify_current_requirement"
    }
  ],
  "options": [
    {"id": "missing_landlord_confirmation", "label": "I do not have landlord confirmation"},
    {"id": "need_form_help", "label": "Help me prepare the form/checklist"},
    {"id": "no_appointment", "label": "I cannot get an appointment"},
    {"id": "talk_to_human", "label": "Talk to a counselor"}
  ],
  "sources": [
    {
      "id": "munich-registration-source",
      "title": "Official Munich registration information",
      "url": "TO_BE_FILLED_FROM_RETRIEVAL",
      "source_type": "municipality",
      "last_updated": "TO_BE_FILLED_FROM_RETRIEVAL",
      "used_for": "registration steps and required documents"
    }
  ],
  "uncertainty": "Requirements must be checked against the current official source before submission.",
  "privacy_receipt": {
    "used_fields": ["city", "housing_status"],
    "stored_fields": [],
    "shared_fields": [],
    "storage_locations": {"city": "local/session", "housing_status": "session"},
    "retention": "session",
    "confidential_processing_used": false,
    "human_shared": false
  }
}
```

## Request Document Preparation

**Input**:

```json
{
  "document_type": "registration_checklist_or_form_support",
  "journey_id": "arrival_munich",
  "required_fields": [
    {
      "name": "full_name",
      "purpose": "Only needed if the user asks for form-support output",
      "storage": "session_only"
    },
    {
      "name": "new_address",
      "purpose": "Only needed to prepare the user's reviewed draft",
      "storage": "session_only"
    }
  ],
  "consent": "pending"
}
```

**Output**:

```json
{
  "status": "needs_user_consent",
  "message": "I can help prepare a draft/checklist. I will use only the fields needed for this document and keep them session-only unless you choose otherwise.",
  "fields_requested": ["full_name", "new_address"],
  "privacy_receipt_preview": {
    "used_fields": ["full_name", "new_address"],
    "stored_fields": [],
    "shared_fields": [],
    "retention": "session only"
  }
}
```

## Human Handoff

**Input**:

```json
{
  "reason": "source_uncertain_or_user_requested",
  "journey_state": {
    "journey_id": "arrival_munich",
    "current_stage": "address_registration",
    "completed_steps": ["orientation", "housing_status"]
  },
  "user_approved_context": {
    "city": "Munich",
    "goal": "Needs help with address registration after finding apartment"
  }
}
```

**Output**:

```json
{
  "handoff_summary": {
    "user_goal": "Needs help with address registration after finding an apartment in Munich.",
    "known_context": ["City: Munich", "Housing status: has apartment"],
    "sources_consulted": ["Official Munich registration information"],
    "open_questions": ["Does the user have current required documents?"],
    "urgency": "normal"
  },
  "requires_user_review": true,
  "raw_chat_included": false,
  "share_status": "blocked_until_user_consents"
}
```
