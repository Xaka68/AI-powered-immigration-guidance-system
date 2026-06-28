import { FileText, Info } from "lucide-react";
import type { Source, StructuredAnswer } from "@/lib/types";
import { SourcesPopup } from "./SourcesPopup";

interface AnswerCardProps {
  answer: StructuredAnswer;
  sources: Source[];
}

export function AnswerCard({ answer, sources }: AnswerCardProps) {
  const hasContent =
    answer.next_steps.length > 0 ||
    answer.documents_needed.length > 0 ||
    !!answer.uncertainty ||
    sources.length > 0;

  if (!hasContent) return null;

  return (
    <article className="space-y-4">
      {answer.next_steps.length > 0 && (
        <section aria-labelledby="next-steps-heading" className="space-y-2">
          <h3
            id="next-steps-heading"
            className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
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
                <span className="text-sm leading-relaxed text-foreground">{step}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      {answer.documents_needed.length > 0 && (
        <section aria-labelledby="docs-heading" className="space-y-2">
          <h3
            id="docs-heading"
            className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Documents to prepare
          </h3>
          <ul className="space-y-1.5">
            {answer.documents_needed.map((doc, i) => (
              <li key={i} className="flex items-start gap-2">
                <FileText
                  className="mt-0.5 h-4 w-4 shrink-0 text-secondary"
                  aria-hidden="true"
                />
                <span className="text-sm leading-relaxed text-foreground">{doc}</span>
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

      <SourcesPopup sources={sources} />
    </article>
  );
}
