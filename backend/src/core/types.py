"""Shared Pydantic models — the typed form of the API contract (PROTOCOL.md §4.1).

These are the single source of truth for the orchestration <-> retrieval seam and
the backend <-> frontend seam. Keep them in lockstep with PROTOCOL.md §4.1/§4.3.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

# --- Sources & answers (the retrieval seam, §4.3) ---------------------------------


class Source(BaseModel):
    """A trusted, citable source page. Freshness (`last_updated`) may be missing."""

    title: str
    url: str
    last_updated: str | None = None
    language: str
    excerpt: str = ""


class StructuredAnswer(BaseModel):
    """A grounded answer. Every next_step/document must be derivable from sources."""

    short_answer: str
    next_steps: list[str] = Field(default_factory=list)
    documents_needed: list[str] = Field(default_factory=list)
    uncertainty: str | None = None


# --- Options (options-first UX, §4.2/§4.1) ----------------------------------------


class Option(BaseModel):
    """A single tappable chip."""

    id: str
    label: str


class OptionSet(BaseModel):
    """A group of chips that fills one slot (used by journey templates / slot filler)."""

    slot: str
    prompt: str
    options: list[Option]
    free_text_fallback: bool = True


# --- Privacy (minimization receipt, §4.1) -----------------------------------------


class PrivacyReceipt(BaseModel):
    used_fields: list[str] = Field(default_factory=list)
    stored_fields: list[str] = Field(default_factory=list)
    storage: str = "local"  # local | session | none
    human_shared: bool = False


# --- Handoff (consent-gated escalation to a human counselor) -----------------------


class HandoffSummary(BaseModel):
    """Counselor-facing summary, built from session — never the raw transcript.
    The user reviews/edits this and consent is gated on the client (Track D7)."""

    user_goal: str
    known_context: list[str] = Field(default_factory=list)
    sources_consulted: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    urgency: str = "normal"


# --- Dynamic journey (LLM-planned, source-grounded; for open-ended goals) ----------


class DynamicState(BaseModel):
    """State of a dynamically-planned journey — built by the LLM from retrieved
    content, walked one step at a time. Lives in the session on the device, like
    the rest of the wallet."""

    goal: str
    roadmap: list[str] = Field(default_factory=list)  # short, ordered step titles
    step_index: int = 0  # which roadmap step the user is on
    pending_slot: str | None = None  # key under which to store the next answer
    facts: dict[str, object] = Field(default_factory=dict)  # what we've learned
    # Conversation memory ([{role, content}]) so follow-ups keep context.
    history: list[dict] = Field(default_factory=list)


# --- Session (the Personal Data Wallet — lives on the client) ----------------------


class Session(BaseModel):
    journey_id: str | None = None
    stage_id: str | None = None
    slots: dict[str, object] = Field(default_factory=dict)
    completed_stages: list[str] = Field(default_factory=list)
    # Set while the user is in a dynamically-planned (non-curated) journey.
    dynamic: DynamicState | None = None


# --- Chat request/response (the frontend seam, §4.1) ------------------------------


class ChatRequest(BaseModel):
    message: str | None = None  # free text; omit if option_id set
    option_id: str | None = None  # tapped chip id; omit if free text
    session: Session | None = None  # echoed from previous response; null on first turn


class ChatResponse(BaseModel):
    journey_id: str | None = None
    stage_id: str | None = None
    assistant_message: str
    options: list[Option] = Field(default_factory=list)
    answer: StructuredAnswer | None = None
    sources: list[Source] = Field(default_factory=list)
    privacy_receipt: PrivacyReceipt = Field(default_factory=PrivacyReceipt)
    requires_handoff: bool = False
    # Present only when requires_handoff is true; the client renders it editable.
    handoff_summary: HandoffSummary | None = None
    # Visible plan for a dynamic journey: the roadmap + which step we're on.
    roadmap: list[str] = Field(default_factory=list)
    roadmap_step: int = 0
    session: Session = Field(default_factory=Session)
