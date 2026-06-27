import type { ConversationTurn, Session } from "./types";

const KEY = "compass_session";

const MAX_HISTORY_TOKENS = 4000;
const CHARS_PER_TOKEN = 4; // rough approximation for token budget

export function trimHistoryToTokenBudget(
  history: ConversationTurn[],
  maxTokens = MAX_HISTORY_TOKENS,
): ConversationTurn[] {
  const maxChars = maxTokens * CHARS_PER_TOKEN;
  let total = 0;
  const kept: ConversationTurn[] = [];
  for (let i = history.length - 1; i >= 0; i--) {
    const n = history[i].content.length;
    if (total + n > maxChars) break;
    kept.unshift(history[i]);
    total += n;
  }
  return kept;
}

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
    window.localStorage.setItem(KEY, JSON.stringify(s));
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
