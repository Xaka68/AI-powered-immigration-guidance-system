"use client";

// Phase 0 seed page (F7). Proves the frontend <-> /chat contract works end to end:
// it starts a journey, shows the assistant message + option chips, and lets you
// tap a chip. Track D (Xavier) replaces/expands this into D2-D8 (chat thread,
// answer cards, privacy receipt, local wallet, handoff panel).

import { useState } from "react";
import { postChat } from "../lib/api";
import type { ChatResponse } from "../lib/types";

export default function Home() {
  const [resp, setResp] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(optionId?: string) {
    setLoading(true);
    setError(null);
    try {
      const r = await postChat({
        option_id: optionId ?? null,
        session: resp?.session ?? null,
      });
      setResp(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "40px auto", padding: "0 16px" }}>
      <h1>Integreat Compass</h1>
      <p style={{ color: "#555" }}>
        Phase 0 seed — wired to <code>/chat</code>. Track D builds the real UI here.
      </p>

      {!resp && (
        <button onClick={() => send()} disabled={loading}>
          {loading ? "..." : "Start"}
        </button>
      )}

      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}

      {resp && (
        <section>
          <p style={{ background: "#f1f5f9", padding: 12, borderRadius: 8 }}>
            {resp.assistant_message}
          </p>

          {resp.answer && (
            <div style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: 12 }}>
              <strong>{resp.answer.short_answer}</strong>
              <ol>
                {resp.answer.next_steps.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ol>
              {resp.sources.map((src, i) => (
                <div key={i} style={{ fontSize: 13, color: "#475569" }}>
                  <a href={src.url} target="_blank" rel="noreferrer">
                    {src.title}
                  </a>{" "}
                  {src.last_updated ? `(updated ${src.last_updated})` : "(date unverified)"}
                </div>
              ))}
            </div>
          )}

          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
            {resp.options.map((o) => (
              <button key={o.id} onClick={() => send(o.id)} disabled={loading}>
                {o.label}
              </button>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
