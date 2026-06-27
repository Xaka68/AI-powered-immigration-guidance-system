// Standalone mock for postChat — lets the frontend run with NO backend.
// Mirrors the Phase 0 backend mock (backend/src/api/main.py) so behavior matches
// what the real API returns. Activated from api.ts via VITE_USE_MOCK / missing VITE_API_URL.
import type { ChatRequest, ChatResponse } from "./types";

function orientation(): ChatResponse {
  return {
    journey_id: null,
    stage_id: "orientation",
    assistant_message:
      "I can help you step by step. What would you like to do first?",
    options: [
      { id: "registration", label: "Register my address" },
      { id: "german_course", label: "Find a German course" },
      { id: "housing", label: "Find a place to live" },
      { id: "human", label: "Talk to a counselor" },
    ],
    answer: null,
    sources: [],
    privacy_receipt: {
      used_fields: [],
      stored_fields: [],
      storage: "local",
      human_shared: false,
    },
    requires_handoff: false,
    requires_agent: false,
    roadmap: [],
    roadmap_step: 0,
    session: {
      journey_id: null,
      stage_id: "orientation",
      slots: {},
      completed_stages: [],
      history: [],
    },
  };
}

function handoff(): ChatResponse {
  return {
    journey_id: "human_counseling",
    stage_id: "human_handoff",
    assistant_message:
      "I can connect you with a human counselor. Review the summary below, then share it when you're ready.",
    options: [],
    answer: null,
    sources: [],
    privacy_receipt: {
      used_fields: ["city"],
      stored_fields: [],
      storage: "local",
      human_shared: false,
    },
    requires_handoff: true,
    requires_agent: false,
    roadmap: [],
    roadmap_step: 0,
    session: {
      journey_id: "human_counseling",
      stage_id: "human_handoff",
      slots: { city: "Munich" },
      completed_stages: ["orientation"],
      history: [],
    },
  };
}

function registrationAnswer(): ChatResponse {
  return {
    journey_id: "address_registration",
    stage_id: "documents",
    assistant_message:
      "Here is what you need to register your address in Munich.",
    options: [
      {
        id: "missing_landlord_confirmation",
        label: "I don't have landlord confirmation",
      },
      { id: "no_appointment", label: "I can't get an appointment" },
      { id: "talk_to_human", label: "Talk to a counselor" },
    ],
    answer: {
      short_answer:
        "After moving into an apartment in Munich, you must register your address (Anmeldung). Prepare your documents and book an appointment.",
      next_steps: [
        "Get a landlord confirmation (Wohnungsgeberbestätigung).",
        "Fill in the registration form (Anmeldung).",
        "Book an appointment at the Bürgerbüro / KVR.",
      ],
      documents_needed: ["Passport", "Landlord confirmation", "Registration form"],
      uncertainty: "This is sample data — verify against the official source.",
    },
    sources: [
      {
        title: "Anmeldung — registering your address (sample)",
        url: "https://example.invalid/anmeldung",
        last_updated: "2025-03-01",
        language: "de",
        excerpt: "Sample source for offline/mock mode.",
      },
    ],
    privacy_receipt: {
      used_fields: ["city"],
      stored_fields: [],
      storage: "local",
      human_shared: false,
    },
    requires_handoff: false,
    requires_agent: false,
    roadmap: [],
    roadmap_step: 0,
    session: {
      journey_id: "address_registration",
      stage_id: "documents",
      slots: { city: "Munich" },
      completed_stages: ["orientation", "housing_status"],
      history: [],
    },
  };
}

export async function mockChat(req: ChatRequest): Promise<ChatResponse> {
  // small delay so the typing indicator shows
  await new Promise((r) => setTimeout(r, 400));

  const session = req.session ?? null;
  const isBootstrap =
    req.option_id == null && !req.message && (session?.journey_id == null);

  if (isBootstrap) return orientation();
  if (req.option_id === "human" || req.option_id === "talk_to_human") {
    return handoff();
  }
  return registrationAnswer();
}
