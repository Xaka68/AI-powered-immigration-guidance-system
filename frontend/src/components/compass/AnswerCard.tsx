import { Check, ExternalLink, FileText, Info, CalendarCheck, CalendarOff } from "lucide-react";
import type { Source, StructuredAnswer } from "@/lib/types";

interface AnswerCardProps {
  answer: StructuredAnswer;
  sources: Source[];
}

export function AnswerCard({ answer, sources }: AnswerCardProps) {
  return (
    <article className="space-y-5 rounded-2xl border border-border bg-card p-5 shadow-sm">
      {answer.short_answer && (
        <p className="text-lg font-semibold leading-snug text-foreground">
          {answer.short_answer}
        </p>
      )}

      {answer.next_steps.length > 0 && (
        <section aria-labelledby="next-steps-heading" className="space-y-2">
          <h3
            id="next-steps-heading"
            className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Next steps
          </h3>
          <ol className="space-y-2">
            {answer.next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-3">
                <span
                  aria-hidden="true"
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary"
                >
                  {i + 1}
                </span>
                <div className="flex flex-1 items-start gap-2">
                  <Check
                    className="mt-1 h-4 w-4 shrink-0 text-success"
                    aria-hidden="true"
                  />
                  <span className="text-sm leading-relaxed text-foreground">
                    {step}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {answer.documents_needed.length > 0 && (
        <section aria-labelledby="docs-heading" className="space-y-2">
          <h3
            id="docs-heading"
            className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Documents to prepare
          </h3>
          <ul className="space-y-2">
            {answer.documents_needed.map((doc, i) => (
              <li key={i} className="flex items-start gap-2">
                <FileText
                  className="mt-0.5 h-4 w-4 shrink-0 text-secondary"
                  aria-hidden="true"
                />
                <span className="text-sm leading-relaxed text-foreground">
                  {doc}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {answer.uncertainty && (
        <div
          role="note"
          className="flex items-start gap-2 rounded-xl border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-foreground"
        >
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
          <span>{answer.uncertainty}</span>
        </div>
      )}

      {sources.length > 0 && (
        <section aria-labelledby="sources-heading" className="space-y-2">
          <h3
            id="sources-heading"
            className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Sources
          </h3>
          <ul className="space-y-2">
            {sources.map((s, i) => {
              const fresh = !!s.last_updated;
              return (
                <li
                  key={i}
                  className="flex flex-col gap-1 rounded-xl border border-border bg-background/60 p-3"
                >
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-start gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:rounded focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <span className="flex-1">{s.title}</span>
                    <ExternalLink
                      className="mt-0.5 h-3.5 w-3.5 shrink-0"
                      aria-hidden="true"
                    />
                  </a>
                  {s.excerpt && (
                    <p className="text-xs text-muted-foreground">{s.excerpt}</p>
                  )}
                  <span
                    className={
                      "mt-1 inline-flex w-fit items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium " +
                      (fresh
                        ? "bg-success/12 text-success"
                        : "bg-warning/15 text-foreground")
                    }
                  >
                    {fresh ? (
                      <>
                        <CalendarCheck className="h-3 w-3" aria-hidden="true" />
                        <span>Updated {s.last_updated}</span>
                      </>
                    ) : (
                      <>
                        <CalendarOff className="h-3 w-3" aria-hidden="true" />
                        <span>Date unverified</span>
                      </>
                    )}
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </article>
  );
}
