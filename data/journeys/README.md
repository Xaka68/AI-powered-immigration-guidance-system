# Authoring a Journey

A journey is **one JSON file** in this folder that validates against
[`schema.json`](./schema.json). The engine directory-scans this folder at
startup — **drop a file in, restart, and it appears.** No code, no config.
Files beginning with `_` (like [`_example.json`](./_example.json)) are ignored.

## Rules (from the constitution)

- **No invented bureaucracy.** Only author steps that a real Integreat page can
  ground. If a step has no source, it should be a `HANDOFF`, not a claim.
- **Don't put source URLs here.** Each content stage has a `retrieval_query`;
  the retrieval layer finds and cites the live page at runtime (so freshness is
  always current).
- **Options-first.** Give each decision an `option_sets` block (the chips).
  `free_text_fallback` stays `true`.

## Shape (see `_example.json` for a complete file)

```jsonc
{
  "id": "address_registration",            // ^[a-z0-9_]+$
  "title": "Register my address (Anmeldung)",
  "description": "…",
  "region": "munich",                       // optional
  "intent_examples": ["I found an apartment", "Anmeldung", "wohnung anmelden"],
  "stages": [
    {
      "id": "housing_status",
      "type": "eligibility_context",        // one of the 8 stage types below
      "goal": "…",
      "required_slots": ["housing_status"],
      "retrieval_query": "…",               // required for CONTENT stages only
      "option_sets": [ /* chips that fill a slot */ ],
      "next_stage_rules": [
        { "if_slot": "housing_status", "equals": "has_apartment", "go_to": "documents" }
      ],
      "escalation_exits": [
        { "condition": "slot:urgency == high", "go_to": "HANDOFF" }
      ]
    }
  ]
}
```

### Stage types

`orientation` · `eligibility_context` · `action_plan` · `documents` ·
`appointment_contact` · `translation_communication` · `follow_up` ·
`human_handoff`

### `go_to` targets

- a **`stage_id`** in this same journey,
- **`ROUTE:<journey_id>`** to jump into another journey,
- **`HANDOFF`** to escalate to a human counselor.

### Content vs. routing stages

A **content stage** (e.g. `action_plan`, `documents`) needs a `retrieval_query`
so it can be grounded. A pure **routing/clarification stage** (e.g.
`eligibility_context` that only asks a question) may omit it.

## Validate before committing

```bash
backend/.venv/bin/python -c "import json,jsonschema; \
  s=json.load(open('data/journeys/schema.json')); \
  jsonschema.validate(json.load(open('data/journeys/YOUR_FILE.json')), s); \
  print('valid')"
```
