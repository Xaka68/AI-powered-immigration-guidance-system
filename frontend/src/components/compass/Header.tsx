import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark } from "./LogoMark";
import { ThemeToggle } from "./ThemeToggle";
import { LANGS, LANG_NAMES } from "@/lib/translations";
import type { Session } from "@/lib/types";

interface HeaderProps {
  session: Session | null;
  onStartOver: () => void;
  onSetLanguage: (lang: string) => void;
  startOverLabel: string;
  privacyTagline: string;
}

function currentLang(session: Session | null): string {
  const lang = session?.slots?.language;
  return typeof lang === "string" && lang ? lang : "en";
}

export function Header({ session, onStartOver, onSetLanguage, startOverLabel, privacyTagline }: HeaderProps) {
  const lang = currentLang(session);

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
            <p className="text-xs text-muted-foreground">{privacyTagline}</p>
          </div>
        </div>

        {/* Always LTR so nav controls stay in consistent order regardless of content direction */}
        <div className="flex items-center gap-2" dir="ltr">
          <select
            value={lang}
            onChange={(e) => onSetLanguage(e.target.value)}
            aria-label="Select language"
            dir="ltr"
            className="rounded-md border border-border bg-card px-2 py-1 text-xs font-medium text-muted-foreground cursor-pointer hover:border-foreground/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {LANGS.map((code) => (
              <option key={code} value={code}>
                {LANG_NAMES[code]}
              </option>
            ))}
          </select>
          <ThemeToggle />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onStartOver}
            className="min-h-11 gap-1.5"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            <span>{startOverLabel}</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
