// Typed client for POST /chat. Track D (Xavier) builds the UI on top of this.
import type { ChatRequest, ChatResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    throw new Error(`/chat failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as ChatResponse;
}
