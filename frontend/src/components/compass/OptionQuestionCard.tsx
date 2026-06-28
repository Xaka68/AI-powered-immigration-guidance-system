import { ArrowRight, UserRound } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Option } from "@/lib/types";
import { cn } from "@/lib/utils";

interface OptionQuestionCardProps {
  options: Option[];
  disabled?: boolean;
  onSelect: (opt: Option) => void;
  onSkip: () => void;
}

function isHumanOption(id: string): boolean {
  return /human|talk_to_human|counselor/i.test(id);
}

// Inline, Claude-style choice panel that pops up only when the assistant offers
// options — replaces the bottom chip row. Keyboard: ↑/↓ move, Enter selects,
// number keys jump, Esc skips. Free text is still typed in the input below.
export function OptionQuestionCard({
  options,
  disabled,
  onSelect,
  onSkip,
}: OptionQuestionCardProps) {
  const [active, setActive] = useState(0);
  const cardRef = useRef<HTMLDivElement>(null);

  // Scroll the panel into view when it appears.
  useEffect(() => {
    cardRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (disabled || options.length === 0) return;
      // Don't hijack keys while the user is typing in the input.
      const tag = (document.activeElement?.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea") return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((a) => Math.min(a + 1, options.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((a) => Math.max(a - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        onSelect(options[active]);
      } else if (e.key === "Escape") {
        e.preventDefault();
        onSkip();
      } else if (/^[1-9]$/.test(e.key)) {
        const i = Number(e.key) - 1;
        if (i < options.length) {
          e.preventDefault();
          onSelect(options[i]);
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [options, active, disabled, onSelect, onSkip]);

  if (options.length === 0) return null;

  return (
    <div
      ref={cardRef}
      role="listbox"
      aria-label="Choose an option"
      className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm"
    >
      <ul className="divide-y divide-border">
        {options.map((opt, i) => {
          const human = isHumanOption(opt.id);
          const isActive = i === active;
          return (
            <li key={opt.id}>
              <button
                type="button"
                role="option"
                aria-selected={isActive}
                disabled={disabled}
                onMouseEnter={() => setActive(i)}
                onClick={() => onSelect(opt)}
                className={cn(
                  "flex w-full items-center gap-3 px-4 py-3 text-start transition-colors",
                  isActive ? "bg-muted" : "hover:bg-muted/60",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-xs font-semibold transition-colors",
                    human
                      ? "bg-accent/15 text-accent"
                      : isActive
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground",
                  )}
                >
                  {human ? <UserRound className="h-3.5 w-3.5" /> : i + 1}
                </span>
                <span
                  className={cn(
                    "flex-1 text-sm leading-snug",
                    human ? "font-medium text-accent" : "text-foreground",
                  )}
                >
                  {opt.label}
                </span>
                <ArrowRight
                  aria-hidden="true"
                  className={cn(
                    "h-4 w-4 shrink-0 text-muted-foreground transition-opacity",
                    isActive ? "opacity-100" : "opacity-0",
                  )}
                />
              </button>
            </li>
          );
        })}
      </ul>

      <div className="flex items-center justify-between gap-3 border-t border-border bg-muted/30 px-4 py-2">
        <span className="hidden text-xs text-muted-foreground sm:inline">
          ↑↓ to navigate · Enter to select · or type below
        </span>
        <button
          type="button"
          onClick={onSkip}
          className="ml-auto rounded-md px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Skip
        </button>
      </div>
    </div>
  );
}
