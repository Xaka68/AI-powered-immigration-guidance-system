import type { ChatRequest, ChatResponse } from "./types";
import { mockChat } from "./mock";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

// Use the standalone mock when explicitly enabled, or when no backend URL is configured.
// - Standalone / preview demo: leave VITE_API_URL unset (or set VITE_USE_MOCK=true) -> mock.
// - Real backend: set VITE_API_URL=http://localhost:8000 -> live fetch.
const USE_MOCK =
  (import.meta.env.VITE_USE_MOCK as string | undefined) === "true" ||
  import.meta.env.VITE_API_URL === undefined;

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  if (USE_MOCK) return mockChat(req);

  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Chat request failed (${res.status})${text ? `: ${text}` : ""}`);
  }
  return (await res.json()) as ChatResponse;
}
