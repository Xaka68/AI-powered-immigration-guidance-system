import type { ChatRequest, ChatResponse, ReasoningStep } from "./types";
import { mockChat } from "./mock";

export interface StreamHandlers {
  onStep: (step: ReasoningStep) => void;
  onDone: (res: ChatResponse) => void;
  onError?: (err: Error) => void;
}

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

// Speech-to-text: send a recorded audio clip to the backend, get the transcript.
export async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  const res = await fetch(`${BASE}/transcribe`, { method: "POST", body: form });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`Transcription failed (${res.status})${t ? `: ${t}` : ""}`);
  }
  const data = (await res.json()) as { text?: string };
  return data.text ?? "";
}

// Stream a turn via SSE: reasoning steps arrive live, then the final response.
// Degrades gracefully to the blocking POST /chat (mock, no body, or fetch error).
export async function streamChat(req: ChatRequest, h: StreamHandlers): Promise<void> {
  if (USE_MOCK) {
    h.onDone(await mockChat(req));
    return;
  }

  let res: Response;
  try {
    res = await fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    h.onDone(await postChat(req)); // network hiccup -> non-stream fallback
    return;
  }
  if (!res.ok || !res.body) {
    h.onDone(await postChat(req));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let sep: number;
    // SSE frames are separated by a blank line.
    while ((sep = buf.indexOf("\n\n")) >= 0) {
      const frame = buf.slice(0, sep);
      buf = buf.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      try {
        if (event === "step") h.onStep(JSON.parse(data) as ReasoningStep);
        else if (event === "done") h.onDone(JSON.parse(data) as ChatResponse);
        else if (event === "error") h.onError?.(new Error(JSON.parse(data).message || "stream error"));
      } catch {
        /* ignore a malformed frame */
      }
    }
  }
}
