export function TypingIndicator() {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Assistant is typing"
      className="inline-flex items-center gap-1.5 rounded-2xl border border-border bg-card px-4 py-3 shadow-sm"
    >
      <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 [animation-delay:0ms]" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60 [animation-delay:300ms]" />
      <span className="sr-only">Loading response…</span>
    </div>
  );
}
