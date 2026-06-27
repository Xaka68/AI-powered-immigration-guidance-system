import { useCallback, useEffect, useRef, useState } from "react";
import { postChat } from "@/lib/api";
import { clearSession, loadSession, saveSession, trimHistoryToTokenBudget } from "@/lib/session";
import type {
  ChatRequest,
  ChatResponse,
  ConversationTurn,
  Option,
  PrivacyReceipt,
  Session,
  Source,
  StructuredAnswer,
} from "@/lib/types";

export type Turn =
  | {
      role: "user";
      id: string;
      text: string;
      lang?: string;
    }
  | {
      role: "assistant";
      id: string;
      text: string;
      answer: StructuredAnswer | null;
      sources: Source[];
      privacyReceipt: PrivacyReceipt;
      requiresHandoff: boolean;
      lang?: string;
    };

export type Status = "idle" | "loading" | "error";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function langFromSession(s: Session | null | undefined): string | undefined {
  const l = s?.slots?.language;
  return typeof l === "string" ? l : undefined;
}

export function useCompass() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [options, setOptions] = useState<Option[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const lastRequestRef = useRef<ChatRequest | null>(null);
  const bootedRef = useRef(false);
  const pendingMessageRef = useRef<string | null>(null);

  const applyResponse = useCallback((res: ChatResponse) => {
    const lang = langFromSession(res.session);
    const now = new Date().toISOString();

    // Append user + assistant turns to the device-local history.
    const prevHistory = res.session.history ?? [];
    const newTurns: ConversationTurn[] = [];
    if (pendingMessageRef.current) {
      newTurns.push({ role: "user", content: pendingMessageRef.current, timestamp: now });
      pendingMessageRef.current = null;
    }
    if (res.assistant_message) {
      newTurns.push({ role: "assistant", content: res.assistant_message, timestamp: now });
    }
    const updatedSession: Session = {
      ...res.session,
      history: trimHistoryToTokenBudget([...prevHistory, ...newTurns]),
    };

    setTurns((prev) => [
      ...prev,
      {
        role: "assistant",
        id: uid(),
        text: res.assistant_message,
        answer: res.answer,
        sources: res.sources,
        privacyReceipt: res.privacy_receipt,
        requiresHandoff: res.requires_handoff,
        lang,
      },
    ]);
    setOptions(res.options ?? []);
    setSession(updatedSession);
    saveSession(updatedSession);
    setStatus("idle");
  }, []);

  const send = useCallback(
    async (req: ChatRequest) => {
      lastRequestRef.current = req;
      setStatus("loading");
      setOptions([]);
      try {
        const res = await postChat(req);
        applyResponse(res);
      } catch (err) {
        console.error(err);
        setStatus("error");
      }
    },
    [applyResponse],
  );

  // initial load — restore session + conversation from localStorage.
  // Clear navigation state (journey_id, stage_id, dynamic) so stale routing from a
  // previous pipeline version never hijacks the context-engine path on reload.
  useEffect(() => {
    if (bootedRef.current) return;
    bootedRef.current = true;
    const existing = loadSession();
    if (!existing) { setSession(null); return; }
    const clean: Session = {
      ...existing,
      journey_id: null,
      stage_id: null,
      dynamic: null,
    };
    setSession(clean);
    saveSession(clean);

    // Rebuild UI turns from history so the conversation reappears on reload (SC-006).
    if (clean.history.length > 0) {
      const emptyReceipt: PrivacyReceipt = {
        used_fields: [],
        stored_fields: [],
        storage: "local",
        human_shared: false,
      };
      setTurns(
        clean.history.map((t) =>
          t.role === "user"
            ? { role: "user", id: uid(), text: t.content }
            : {
                role: "assistant",
                id: uid(),
                text: t.content,
                answer: null,
                sources: [],
                privacyReceipt: emptyReceipt,
                requiresHandoff: false,
              },
        ),
      );
    }
  }, []);

  const selectOption = useCallback(
    (opt: Option) => {
      const lang = langFromSession(session);
      setTurns((prev) => [
        ...prev,
        { role: "user", id: uid(), text: opt.label, lang },
      ]);
      void send({ option_id: opt.id, session });
    },
    [send, session],
  );

  const sendText = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      pendingMessageRef.current = trimmed;
      const lang = langFromSession(session);
      setTurns((prev) => [
        ...prev,
        { role: "user", id: uid(), text: trimmed, lang },
      ]);
      // Send current session — history holds all PREVIOUS turns; the current
      // user message is in req.message so context_engine sees it separately.
      void send({ message: trimmed, session });
    },
    [send, session],
  );

  const retry = useCallback(() => {
    if (lastRequestRef.current) void send(lastRequestRef.current);
  }, [send]);

  const startOver = useCallback(() => {
    clearSession();
    setTurns([]);
    setOptions([]);
    setSession(null);
  }, []);

  return {
    turns,
    options,
    session,
    status,
    selectOption,
    sendText,
    retry,
    startOver,
  };
}
