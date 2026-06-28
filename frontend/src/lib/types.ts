export interface Option {
  id: string;
  label: string;
}

export interface Source {
  title: string;
  url: string;
  last_updated: string | null;
  language: string;
  excerpt?: string;
}

export interface StructuredAnswer {
  short_answer: string;
  next_steps: string[];
  documents_needed: string[];
  uncertainty: string | null;
}

export interface PrivacyReceipt {
  used_fields: string[];
  stored_fields: string[];
  storage: "local" | "session" | "none";
  human_shared: boolean;
  // true = this turn's query was processed by a third-party LLM (data left the
  // device's trust boundary); false = self-hosted, nothing left it.
  external_llm?: boolean;
}

// State of a dynamically-planned (non-curated) journey. Treat as opaque on the
// client — just persist it in the session and echo it back each turn.
export interface DynamicState {
  goal: string;
  roadmap: string[];
  step_index: number;
  pending_slot: string | null;
  facts: Record<string, unknown>;
}

export interface Session {
  journey_id: string | null;
  stage_id: string | null;
  slots: Record<string, unknown>;
  completed_stages: string[];
  dynamic?: DynamicState | null;
}

// Counselor-facing summary (built by the backend from session, never raw chat).
// Present only when requires_handoff is true. Rendered editable + consent-gated in D7.
export interface HandoffSummary {
  user_goal: string;
  known_context: string[];
  sources_consulted: string[];
  open_questions: string[];
  urgency: string;
}

export interface ChatRequest {
  message?: string | null;
  option_id?: string | null;
  session?: Session | null;
}

export interface ChatResponse {
  journey_id: string | null;
  stage_id: string | null;
  assistant_message: string;
  options: Option[];
  answer: StructuredAnswer | null;
  sources: Source[];
  privacy_receipt: PrivacyReceipt;
  requires_handoff: boolean;
  handoff_summary?: HandoffSummary | null;
  // Visible plan for a dynamic journey: the roadmap + which step we're on.
  // Render as a progress checklist; empty for curated journeys / welcome.
  roadmap: string[];
  roadmap_step: number;
  session: Session;
}
