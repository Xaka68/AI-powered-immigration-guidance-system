import { useEffect, useRef } from "react";
import { AgentConsentCard } from "./AgentConsentCard";
import { AnswerCard } from "./AnswerCard";
import { ErrorRetry } from "./ErrorRetry";
import { HandoffPanel } from "./HandoffPanel";
import { PrivacyReceipt } from "./PrivacyReceipt";
import { TypingIndicator } from "./TypingIndicator";
import { isRTL } from "@/lib/rtl";
import type { Session } from "@/lib/types";
import type { Status, Turn } from "@/hooks/use-compass";

interface ChatThreadProps {
  turns: Turn[];
  status: Status;
  session: Session | null;
  onRetry: () => void;
  onConfirmAgent: (agentId: string, turnId: string) => void;
  onDeclineAgent: (turnId: string) => void;
}

export function ChatThread({ turns, status, session, onRetry, onConfirmAgent, onDeclineAgent }: ChatThreadProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, status]);

  return (
    <div className="flex flex-col gap-4">
      {turns.map((turn) => {
        const rtl = isRTL(turn.lang);
        if (turn.role === "user") {
          return (
            <div key={turn.id} className="flex justify-end">
              <div
                dir={rtl ? "rtl" : undefined}
                className="max-w-[85%] rounded-2xl border border-primary/20 bg-primary/10 px-4 py-2.5 text-start text-base text-foreground shadow-sm"
              >
                {turn.text}
              </div>
            </div>
          );
        }
        return (
          <div key={turn.id} className="flex flex-col gap-2">
            <div className="flex justify-start">
              <div
                dir={rtl ? "rtl" : undefined}
                className="max-w-[90%] rounded-2xl border border-border bg-card px-4 py-3 text-start text-base text-foreground shadow-sm"
              >
                {turn.text}
              </div>
            </div>
            {turn.answer && (
              <div dir={rtl ? "rtl" : undefined}>
                <AnswerCard answer={turn.answer} sources={turn.sources} />
              </div>
            )}
            {turn.requiresHandoff && (
              <div dir={rtl ? "rtl" : undefined}>
                <HandoffPanel
                  id={`handoff-${turn.id}`}
                  session={session}
                  answer={turn.answer}
                  assistantMessage={turn.text}
                />
              </div>
            )}
            {turn.agentSuggestion && (
              <div dir={rtl ? "rtl" : undefined}>
                <AgentConsentCard
                  suggestion={turn.agentSuggestion}
                  onConfirm={() => onConfirmAgent(turn.agentSuggestion!.agent_id, turn.id)}
                  onDecline={() => onDeclineAgent(turn.id)}
                />
              </div>
            )}
            <div dir={rtl ? "rtl" : undefined}>
              <PrivacyReceipt receipt={turn.privacyReceipt} id={`pr-${turn.id}`} />
            </div>
          </div>
        );
      })}

      {status === "loading" && (
        <div className="flex justify-start">
          <TypingIndicator />
        </div>
      )}

      {status === "error" && (
        <div className="flex justify-start">
          <ErrorRetry onRetry={onRetry} />
        </div>
      )}

      <div ref={endRef} aria-hidden="true" />
    </div>
  );
}
