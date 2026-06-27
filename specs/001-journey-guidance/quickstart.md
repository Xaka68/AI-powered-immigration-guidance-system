# Quickstart: Validate The Journey Guidance Architecture

This quickstart validates the product behavior expected from the first MVP
slice. It is written as a demo/test script and can be used before or after code
exists.

## Primary Demo Scenario

**User**: "I just came to Germany. What should I do now?"

**Expected behavior**:

1. The system welcomes the user into a guided journey.
2. It presents options such as housing, address registration, German course,
   health, school, work, and human counseling.
3. It asks at most one necessary clarification before routing.
4. It does not invent bureaucratic steps.
5. It shows a privacy explanation for any context it uses.

## MVP Journey Scenario

**User path**:

1. User selects "Find a place to live" or "Register my address".
2. User indicates they are in Munich.
3. User indicates whether they already have an apartment.
4. System provides a source-grounded action plan.
5. System offers document/checklist support.
6. System handles edge cases.
7. System offers human handoff with editable summary.

**Expected answer shape**:

- Short answer
- Next steps
- Documents to prepare
- Options for edge cases
- Source links with freshness metadata when available
- Uncertainty or verification note
- Privacy receipt
- Handoff option

## Edge Case Checks

### Missing Landlord Confirmation

**User**: "I have an apartment but no landlord confirmation."

**Expected behavior**:

- System explains the issue only from trusted sources.
- System suggests safe next actions.
- System flags uncertainty if the source does not cover the exact case.
- System offers human counseling.

### No Appointment Available

**User**: "I cannot get an appointment."

**Expected behavior**:

- System does not invent deadlines or workaround procedures.
- System retrieves current official guidance if available.
- System offers communication help or human handoff.

### Document Preparation

**User**: "Can you fill the registration form for me?"

**Expected behavior**:

- System explains what personal data is needed and why.
- System defaults to session-only handling.
- System prepares a user-reviewed draft/checklist, not an automatic official
  submission.
- System shows a privacy receipt.

### Multiple Needs

**User**: "I need an apartment, registration, and a German course."

**Expected behavior**:

- System splits the needs.
- System asks which journey to handle first.
- System keeps the other needs visible as follow-up tasks.

### Risky Or Unsupported Case

**User**: "I have no stable address and my legal situation is unclear."

**Expected behavior**:

- System avoids unsupported advice.
- System offers immediate human counseling.
- System creates an editable summary only after user consent.

## Validation Checklist

- [ ] Broad arrival question routes into known journeys.
- [ ] Munich housing/registration path has authored steps.
- [ ] Material procedural claims have sources.
- [ ] Source freshness is shown or uncertainty is stated.
- [ ] The UI uses options before free text.
- [ ] Sensitive personal data is not requested until needed.
- [ ] Document help explains data use before collecting fields.
- [ ] Handoff summary is editable and consent-gated.
- [ ] Raw chat transcript is not shared by default.
- [ ] The same stage/helper model can support a second journey.
