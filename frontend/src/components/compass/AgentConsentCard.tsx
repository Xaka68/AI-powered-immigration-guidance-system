import { Sparkles } from "lucide-react";
import type { AgentSuggestion } from "@/lib/types";

interface AgentConsentCardProps {
  suggestion: AgentSuggestion;
  onConfirm: () => void;
  onDecline: () => void;
}

export function AgentConsentCard({ suggestion, onConfirm, onDecline }: AgentConsentCardProps) {
  return (
    <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4 space-y-3">
      <div className="flex items-start gap-2">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-foreground">{suggestion.label}</p>
          <p className="mt-1 text-sm text-muted-foreground">{suggestion.description}</p>
        </div>
      </div>

      {suggestion.data_needed.length > 0 && (
        <p className="text-xs text-muted-foreground pl-6">
          Uses: {suggestion.data_needed.join(", ")}
        </p>
      )}

      <div className="flex gap-2 pl-6">
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-lg bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Yes, let's do it
        </button>
        <button
          type="button"
          onClick={onDecline}
          className="rounded-lg border border-border px-4 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Not now
        </button>
      </div>
    </div>
  );
}
