import { UserRound } from "lucide-react";
import type { Option } from "@/lib/types";
import { cn } from "@/lib/utils";

interface OptionChipsProps {
  options: Option[];
  disabled?: boolean;
  onSelect: (opt: Option) => void;
}

function isHumanOption(id: string): boolean {
  return /human|talk_to_human|counselor/i.test(id);
}

export function OptionChips({ options, disabled, onSelect }: OptionChipsProps) {
  if (!options.length) return null;
  return (
    <div
      role="group"
      aria-label="Suggested replies"
      className="flex flex-wrap gap-2"
    >
      {options.map((opt) => {
        const human = isHumanOption(opt.id);
        return (
          <button
            key={opt.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(opt)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg border px-3.5 py-1.5 text-start text-sm font-medium transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100",
              human
                ? "border-accent/40 bg-accent/10 text-accent hover:bg-accent/15"
                : "border-border bg-card text-foreground hover:border-foreground/30 hover:bg-muted",
            )}
          >
            {human && <UserRound className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
