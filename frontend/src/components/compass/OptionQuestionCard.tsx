import { ArrowRight, Pencil, UserRound } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Option } from "@/lib/types";
import { cn } from "@/lib/utils";

interface OptionQuestionCardProps {
  options: Option[];
  disabled?: boolean;
  onSelect: (opt: Option) => void;
  /** Submit a free-text answer typed inline (e.g. for an "I'll enter my city" option). */
  onSubmitText: (text: string) => void;
  onSkip: () => void;
  orTypeItLabel?: string;
  skipLabel?: string;
}

function isHumanOption(id: string): boolean {
  return /human|talk_to_human|counselor/i.test(id);
}

// An "enter / type my own …" option: instead of committing a fixed choice, the
// user should type a value right here in the panel.
function isFreeTextOption(opt: Option): boolean {
  return (
    /\b(enter|type|specify|write|provide)\b/i.test(opt.label) ||
    /(^|_)(other|custom|free[_-]?text|manual|enter)(_|$)/i.test(opt.id)
  );
}

// "I'll enter my city" -> "Type your city…"; falls back to a generic prompt.
function placeholderFor(label: string): string {
  const m = label.match(/(?:enter|type|specify|provide|write)\s+(?:my|your)\s+(.+)/i);
  return m ? `Type your ${m[1].replace(/[.…]+$/, "").trim()}…` : "Type your answer…";
}

// Inline, Claude-style choice panel that pops up only when the assistant offers
// options. Keyboard: ↑/↓ move, Enter selects, number keys jump, Esc skips. A
// "type my own" option opens an inline input that submits as free text.
export function OptionQuestionCard({
  options,
  disabled,
  onSelect,
  onSubmitText,
  onSkip,
  orTypeItLabel = "Or type it",
  skipLabel = "Skip",
}: OptionQuestionCardProps) {
  const [active, setActive] = useState(0);
  const [inputFor, setInputFor] = useState<string | null>(null);
  const [value, setValue] = useState("");
  const cardRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll the panel into view when it appears.
  useEffect(() => {
    cardRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, []);

  // Focus the inline input as soon as a free-text option is activated.
  useEffect(() => {
    if (inputFor) inputRef.current?.focus();
  }, [inputFor]);

  // Activate an option: free-text ones open the inline input; the rest commit.
  function activate(opt: Option) {
    if (disabled) return;
    if (isFreeTextOption(opt)) {
      setInputFor(opt.id);
      setValue("");
    } else {
      onSelect(opt);
    }
  }

  function submitInput() {
    const v = value.trim();
    if (!v) return;
    onSubmitText(v);
    setInputFor(null);
    setValue("");
  }

  // The always-present "Or type it" affordance: a free-text answer used as the
  // next message, regardless of the options the LLM offered.
  const TYPE_ID = "__type_it__";

  function inputRow(key: string, placeholder: string) {
    return (
      <li key={key}>
        <div className="flex items-center gap-3 px-4 py-3">
          <span
            aria-hidden="true"
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground"
          >
            <Pencil className="h-3.5 w-3.5" />
          </span>
          <input
            ref={inputRef}
            type="text"
            value={value}
            disabled={disabled}
            placeholder={placeholder}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                submitInput();
              } else if (e.key === "Escape") {
                e.preventDefault();
                setInputFor(null);
                setValue("");
              }
            }}
            className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
          <button
            type="button"
            aria-label="Submit"
            disabled={disabled || !value.trim()}
            onClick={submitInput}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground transition-opacity disabled:opacity-40"
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </li>
    );
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (disabled || options.length === 0) return;
      // Don't hijack keys while the user is typing (input/textarea has focus).
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
        activate(options[active]);
      } else if (e.key === "Escape") {
        e.preventDefault();
        onSkip();
      } else if (/^[1-9]$/.test(e.key)) {
        const i = Number(e.key) - 1;
        if (i < options.length) {
          e.preventDefault();
          activate(options[i]);
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options, active, disabled, onSkip]);

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
          const freeText = isFreeTextOption(opt);
          const isActive = i === active;

          // Inline input mode for a "type my own" option.
          if (inputFor === opt.id) return inputRow(opt.id, placeholderFor(opt.label));

          return (
            <li key={opt.id}>
              <button
                type="button"
                role="option"
                aria-selected={isActive}
                disabled={disabled}
                onMouseEnter={() => setActive(i)}
                onClick={() => activate(opt)}
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
                  {human ? (
                    <UserRound className="h-3.5 w-3.5" />
                  ) : freeText ? (
                    <Pencil className="h-3.5 w-3.5" />
                  ) : (
                    i + 1
                  )}
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

        {/* Always offer a free-text answer, whatever options the LLM gave. */}
        {inputFor === TYPE_ID ? (
          inputRow(TYPE_ID, "Type your answer…")
        ) : (
          <li key={TYPE_ID}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => {
                setInputFor(TYPE_ID);
                setValue("");
              }}
              className="flex w-full items-center gap-3 px-4 py-3 text-start transition-colors hover:bg-muted/60 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span
                aria-hidden="true"
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground"
              >
                <Pencil className="h-3.5 w-3.5" />
              </span>
              <span className="flex-1 text-sm leading-snug text-muted-foreground">
                {orTypeItLabel}
              </span>
            </button>
          </li>
        )}
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
          {skipLabel}
        </button>
      </div>
    </div>
  );
}
