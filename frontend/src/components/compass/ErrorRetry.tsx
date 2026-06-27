import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorRetryProps {
  onRetry: () => void;
}

export function ErrorRetry({ onRetry }: ErrorRetryProps) {
  return (
    <button
      type="button"
      onClick={onRetry}
      className="flex w-full items-start gap-3 rounded-2xl border border-warning/50 bg-warning/10 px-4 py-3 text-start text-sm text-foreground shadow-sm transition hover:bg-warning/15 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <AlertTriangle
        className="mt-0.5 h-5 w-5 shrink-0 text-warning"
        aria-hidden="true"
      />
      <span className="flex-1">
        <span className="block font-semibold">Something went wrong</span>
        <span className="text-muted-foreground">Tap to retry the last step.</span>
      </span>
      <RefreshCw className="mt-0.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
    </button>
  );
}
