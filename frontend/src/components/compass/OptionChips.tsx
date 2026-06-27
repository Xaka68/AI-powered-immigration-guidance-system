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
              "inline-flex min-h-12 items-center gap-2 rounded-full border px-4 py-2.5 text-start text-base font-medium shadow-sm transition",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              "active:scale-[0.98]",
              "disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100",
              human
                ? "border-accent/30 bg-accent/10 text-accent hover:bg-accent/15"
                : "border-primary/20 bg-primary/8 text-primary hover:bg-primary/12",
            )}
            style={
              human
                ? undefined
                : { backgroundColor: "color-mix(in oklab, var(--primary) 8%, white)" }
            }
          >
            {human && <UserRound className="h-4 w-4 shrink-0" aria-hidden="true" />}
            <span>{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
