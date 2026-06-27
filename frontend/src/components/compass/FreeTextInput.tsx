import { Send } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FreeTextInputProps {
  disabled?: boolean;
  label?: string;
  onSubmit: (text: string) => void;
}

export function FreeTextInput({ disabled, label, onSubmit }: FreeTextInputProps) {
  const [value, setValue] = useState("");

  function handle(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form
      onSubmit={handle}
      className="flex items-end gap-2"
    >
      <div className="flex-1">
        <Label
          htmlFor="compass-free-text"
          className="mb-1 block text-xs font-medium text-muted-foreground"
        >
          {label ?? "Or type your question"}
        </Label>
        <Input
          id="compass-free-text"
          type="text"
          inputMode="text"
          autoComplete="off"
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask in your own words…"
          className="min-h-11 bg-card text-base"
        />
      </div>
      <Button
        type="submit"
        size="icon"
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        className="min-h-11 min-w-11"
      >
        <Send className="h-4 w-4" aria-hidden="true" />
      </Button>
    </form>
  );
}
