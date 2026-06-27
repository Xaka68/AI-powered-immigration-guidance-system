"""FastAPI app.

Phase 0 (F5): `/chat` returns a hardcoded, contract-shaped ChatResponse so the
frontend (Track D) can build immediately. Track A (A6) replaces the mock body
with the real router -> graph -> retrieval pipeline. The request/response shapes
(PROTOCOL.md §4.1) do NOT change when that happens.

Run from repo root:
    uvicorn api.main:app --app-dir backend/src --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.types import (
    ChatRequest,
    ChatResponse,
    Option,
    PrivacyReceipt,
    Session,
    Source,
    StructuredAnswer,
)

app = FastAPI(title="Integreat Compass API", version="0.1.0")

# Frontend dev server runs on another origin; allow it during the hackathon.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """MOCK pipeline (F5). Returns deterministic contract-shaped data.

    First turn (no session) -> orientation with journey-choice chips.
    After a chip is tapped   -> a sample grounded answer for address registration.
    """
    session = req.session or Session()

    # First contact: route the broad arrival question into options-first choices.
    if session.journey_id is None and req.option_id is None:
        return ChatResponse(
            journey_id=None,
            stage_id="orientation",
            assistant_message=(
                "I can help you step by step. What would you like to do first?"
            ),
            options=[
                Option(id="registration", label="Register my address"),
                Option(id="german_course", label="Find a German course"),
                Option(id="housing", label="Find a place to live"),
                Option(id="human", label="Talk to a counselor"),
            ],
            answer=None,
            sources=[],
            privacy_receipt=PrivacyReceipt(used_fields=[], storage="local"),
            requires_handoff=False,
            session=Session(stage_id="orientation"),
        )

    # Any subsequent turn: a sample grounded answer (mock content).
    return ChatResponse(
        journey_id="address_registration",
        stage_id="documents",
        assistant_message="Here is what you need to register your address in Munich.",
        options=[
            Option(id="missing_landlord_confirmation", label="I don't have landlord confirmation"),
            Option(id="no_appointment", label="I can't get an appointment"),
            Option(id="talk_to_human", label="Talk to a counselor"),
        ],
        answer=StructuredAnswer(
            short_answer=(
                "After moving into an apartment in Munich, you must register your "
                "address (Anmeldung). Prepare your documents and book an appointment."
            ),
            next_steps=[
                "Get a landlord confirmation (Wohnungsgeberbestätigung).",
                "Fill in the registration form (Anmeldung).",
                "Book an appointment at the Bürgerbüro / KVR.",
            ],
            documents_needed=["Passport", "Landlord confirmation", "Registration form"],
            uncertainty="This is mock data — verify against the official source.",
        ),
        sources=[
            Source(
                title="Anmeldung — registering your address (MOCK)",
                url="https://example.invalid/anmeldung",
                last_updated="2025-03-01",
                language="de",
                excerpt="Mock source for Phase 0.",
            )
        ],
        privacy_receipt=PrivacyReceipt(
            used_fields=["city"], stored_fields=[], storage="local", human_shared=False
        ),
        requires_handoff=False,
        session=Session(
            journey_id="address_registration",
            stage_id="documents",
            slots={"city": "Munich"},
            completed_stages=["orientation", "housing_status"],
        ),
    )
