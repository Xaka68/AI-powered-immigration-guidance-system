import { useState, useEffect, useRef } from "react";
import { ExternalLink } from "lucide-react";
import type { Source } from "@/lib/types";

interface SourcesPopupProps {
  sources: Source[];
}

export function SourcesPopup({ sources }: SourcesPopupProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [open]);

  if (sources.length === 0) return null;

  return (
    <div ref={containerRef} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground hover:bg-muted/80 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ExternalLink className="h-3 w-3" aria-hidden="true" />
        Sources ({sources.length})
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Sources"
          className="absolute bottom-full left-0 z-50 mb-2 min-w-[16rem] max-w-xs rounded-xl border border-border bg-card p-3 shadow-lg"
        >
          <ul className="space-y-2">
            {sources.map((s, i) => (
              <li key={i}>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-start gap-1.5 text-sm text-primary underline-offset-4 hover:underline focus-visible:rounded focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <span className="flex-1 leading-snug">{s.title}</span>
                  <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
