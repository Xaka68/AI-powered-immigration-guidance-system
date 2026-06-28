import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark } from "./LogoMark";
import { ThemeToggle } from "./ThemeToggle";
import type { Session } from "@/lib/types";

interface HeaderProps {
  session: Session | null;
  onStartOver: () => void;
}

function languageLabel(session: Session | null): string {
  const lang = session?.slots?.language;
  if (typeof lang !== "string" || !lang) return "EN";
  return lang.toUpperCase();
}

export function Header({ session, onStartOver }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
      <div className="flex w-full items-center justify-between gap-3 px-4 sm:px-8 lg:px-12 py-3">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground"
          >
            <LogoMark className="h-5 w-5" />
          </span>
          <div className="leading-tight">
            <h1 className="font-display text-base font-semibold text-foreground">
              Integreat Compass
            </h1>
            <p className="text-xs text-muted-foreground">
              Trusted guidance · your data stays on this device
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            aria-label="Current language"
            className="rounded-md border border-border bg-card px-2 py-1 text-xs font-medium text-muted-foreground"
          >
            {languageLabel(session)}
          </span>
          <ThemeToggle />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onStartOver}
            className="min-h-11 gap-1.5"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            <span>Start over</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
