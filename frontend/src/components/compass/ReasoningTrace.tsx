import {
  AlertTriangle,
  Brain,
  Check,
  ChevronDown,
  Globe,
  Loader2,
  MessageCircleQuestion,
  ScanText,
  Search,
  Sparkles,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import type { ReasoningStep } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ReasoningTraceProps {
  steps: ReasoningStep[];
  /** Live (in-progress) vs. a finished, collapsible trace on a past turn. */
  live?: boolean;
  /** Total time spent reasoning, ms — shown in the collapsed header. */
  thoughtMs?: number;
}

function meta(s: ReasoningStep): { icon: LucideIcon; label: string; warn?: boolean } {
  switch (s.type) {
    case "search":
      return s.source === "web"
        ? { icon: Globe, label: "Searching the web" }
        : { icon: Search, label: "Searching official information" };
    case "search_result":
      return { icon: Check, label: `Found ${s.count ?? 0} source${s.count === 1 ? "" : "s"}` };
    case "error":
      return { icon: AlertTriangle, label: s.label || "No results", warn: true };
    case "reviewing":
      return { icon: ScanText, label: "Reviewing sources" };
    case "ask":
      return { icon: MessageCircleQuestion, label: "Preparing a question" };
    case "answer":
      return { icon: Sparkles, label: "Writing the answer" };
    case "handoff":
      return { icon: UserRound, label: "Connecting you with a counselor" };
    case "thinking":
    default:
      return { icon: Brain, label: "Thinking" };
  }
}

function formatDuration(ms?: number): string {
  if (!ms || ms < 1000) return "a moment";
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function Timeline({ steps, live }: { steps: ReasoningStep[]; live?: boolean }) {
  return (
    <ol className="space-y-2.5">
      {steps.map((s, i) => {
        const { icon: Icon, label, warn } = meta(s);
        const isLast = i === steps.length - 1;
        const active = live && isLast; // the step currently running
        const spinning = active && (s.type === "thinking" || s.type === "reviewing");
        return (
          <li key={i} className="flex items-start gap-2.5">
            <span
              aria-hidden="true"
              className={cn(
                "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                warn
                  ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                  : active
                    ? "bg-primary/15 text-primary"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {spinning ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Icon className="h-3 w-3" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <span
                className={cn(
                  "text-sm",
                  warn
                    ? "text-amber-600 dark:text-amber-400"
                    : active
                      ? "text-foreground"
                      : "text-muted-foreground",
                  active && "animate-pulse",
                )}
              >
                {label}
                {active && !warn && s.type !== "search" ? "…" : ""}
              </span>
              {s.query && (
                <span className="ms-2 inline-block max-w-full truncate rounded-md bg-muted px-1.5 py-0.5 align-middle text-xs text-muted-foreground">
                  {s.query}
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

// Renders the agent's reasoning as a step-by-step timeline. While the turn is in
// flight it streams open and live; once done it collapses to a small
// "Thought for Xs · N steps" line the user can expand.
export function ReasoningTrace({ steps, live, thoughtMs }: ReasoningTraceProps) {
  const [open, setOpen] = useState(false);
  if (steps.length === 0) return null;

  if (live) {
    return (
      <div className="rounded-xl border border-border bg-card/60 px-3.5 py-3">
        <Timeline steps={steps} live />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card/40">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3.5 py-2 text-start text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <Brain className="h-3.5 w-3.5 shrink-0" />
        <span>
          Thought for {formatDuration(thoughtMs)} · {steps.length} step
          {steps.length === 1 ? "" : "s"}
        </span>
        <ChevronDown
          className={cn("ms-auto h-4 w-4 transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="border-t border-border px-3.5 py-3">
          <Timeline steps={steps} />
        </div>
      )}
    </div>
  );
}
