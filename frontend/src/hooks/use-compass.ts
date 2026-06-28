import { useCallback, useEffect, useRef, useState } from "react";
import { postChat } from "@/lib/api";
import { clearSession, loadSession, saveSession } from "@/lib/session";
import type {
  ChatRequest,
  ChatResponse,
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

  const applyResponse = useCallback((res: ChatResponse) => {
    const lang = langFromSession(res.session);
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
    setSession(res.session);
    saveSession(res.session);
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

  // initial load — restore the session's slots but DON'T auto-send. The welcome
  // screen (empty turns) is the landing; the user starts the conversation by
  // tapping a quick-start chip or typing. Guard against StrictMode double-run.
  useEffect(() => {
    if (bootedRef.current) return;
    bootedRef.current = true;
    const existing = loadSession();
    // Reset journey position on reload but preserve extracted slots (city,
    // language) so the agent keeps context once the user starts.
    setSession(existing ? { ...existing, journey_id: null, stage_id: null } : null);
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
      const lang = langFromSession(session);
      setTurns((prev) => [
        ...prev,
        { role: "user", id: uid(), text: trimmed, lang },
      ]);
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
    setStatus("idle");
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
