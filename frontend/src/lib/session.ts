import type { Session } from "./types";

const KEY = "compass_session";

export function loadSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function saveSession(s: Session): void {
  if (typeof window === "undefined") return;
  try {
    // Persist the lightweight wallet ONLY — never the conversation memory
    // (`dynamic`, which holds chat history). Each page load / new chat therefore
    // starts a fresh conversation, so a previous conversation can never bleed
    // into another. Within a conversation, memory lives in in-app state.
    const { dynamic: _dropped, ...persistable } = s;
    window.localStorage.setItem(KEY, JSON.stringify(persistable));
  } catch {
    // ignore quota / privacy mode errors
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
