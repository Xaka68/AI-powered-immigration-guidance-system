import { useEffect, useRef } from "react";
import { AnswerCard } from "./AnswerCard";
import { ErrorRetry } from "./ErrorRetry";
import { HandoffPanel } from "./HandoffPanel";
import { LogoMark } from "./LogoMark";
import { PrivacyReceipt } from "./PrivacyReceipt";
import { ReasoningTrace } from "./ReasoningTrace";
import { TypingIndicator } from "./TypingIndicator";
import { isRTL } from "@/lib/rtl";
import type { ReasoningStep, Session } from "@/lib/types";
import type { Status, Turn } from "@/hooks/use-compass";

interface ChatThreadProps {
  turns: Turn[];
  status: Status;
  session: Session | null;
  steps: ReasoningStep[];
  onRetry: () => void;
}

function CompassAvatar() {
  return (
    <span
      aria-hidden="true"
      className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary"
    >
      <LogoMark className="h-4 w-4" />
    </span>
  );
}

export function ChatThread({ turns, status, session, steps, onRetry }: ChatThreadProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, status]);

  return (
    <div className="flex flex-col gap-1">
      {turns.map((turn) => {
        const rtl = isRTL(turn.lang);
        if (turn.role === "user") {
          return (
            <div key={turn.id} className="flex justify-end py-1">
              <div
                dir={rtl ? "rtl" : undefined}
                className="max-w-[80%] rounded-3xl bg-muted px-4 py-2.5 text-base text-foreground"
              >
                {turn.text}
              </div>
            </div>
          );
        }
        return (
          <div key={turn.id} className="flex items-start gap-3 py-3">
            <CompassAvatar />
            <div dir={rtl ? "rtl" : undefined} className="flex-1 min-w-0 space-y-3">
              {turn.steps && turn.steps.length > 0 && (
                <ReasoningTrace steps={turn.steps} thoughtMs={turn.thoughtMs} />
              )}
              {turn.text && (
                <p className="text-base leading-relaxed text-foreground">{turn.text}</p>
              )}
              {turn.answer && (
                <AnswerCard answer={turn.answer} sources={turn.sources} />
              )}
              {turn.requiresHandoff && (
                <HandoffPanel
                  id={`handoff-${turn.id}`}
                  session={session}
                  answer={turn.answer}
                  assistantMessage={turn.text}
                />
              )}
              <PrivacyReceipt receipt={turn.privacyReceipt} id={`pr-${turn.id}`} />
            </div>
          </div>
        );
      })}

      {status === "loading" && (
        <div className="flex items-start gap-3 py-3">
          <CompassAvatar />
          <div className="flex-1 min-w-0">
            {steps.length > 0 ? (
              <ReasoningTrace steps={steps} live />
            ) : (
              <TypingIndicator />
            )}
          </div>
        </div>
      )}

      {status === "error" && (
        <div className="flex items-start gap-3 py-3">
          <CompassAvatar />
          <ErrorRetry onRetry={onRetry} />
        </div>
      )}

      <div ref={endRef} aria-hidden="true" />
    </div>
  );
}
