import { Send } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

interface FreeTextInputProps {
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  onSubmit: (text: string) => void;
}

export function FreeTextInput({ disabled, label, placeholder, onSubmit }: FreeTextInputProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const prevDisabledRef = useRef(disabled);

  // Auto-focus when the loading state clears (disabled true → false).
  // Skips the first render so we don't steal focus on page load.
  useEffect(() => {
    if (prevDisabledRef.current && !disabled) {
      inputRef.current?.focus();
    }
    prevDisabledRef.current = disabled;
  }, [disabled]);

  function handle(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form onSubmit={handle} className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor="compass-free-text"
          className="text-xs font-medium text-muted-foreground"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          id="compass-free-text"
          type="text"
          inputMode="text"
          autoComplete="off"
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder ?? "Ask in your own words…"}
          className="w-full rounded-full border border-foreground/25 bg-card py-3 pl-5 pr-14 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="absolute right-2 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </form>
  );
}
