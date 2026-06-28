import { Info } from "lucide-react";
import type { AnswerSection, Source, StructuredAnswer } from "@/lib/types";
import { SourcesPopup } from "./SourcesPopup";

interface AnswerCardProps {
  answer: StructuredAnswer;
  sources: Source[];
}

export function AnswerCard({ answer, sources }: AnswerCardProps) {
  const sections = answer.sections ?? [];
  const hasContent =
    sections.length > 0 || !!answer.uncertainty || sources.length > 0;

  if (!hasContent) return null;

  return (
    <article className="space-y-4">
      {sections.map((section, i) => (
        <SectionBlock key={i} section={section} index={i} />
      ))}

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

function SectionBlock({ section, index }: { section: AnswerSection; index: number }) {
  const items = section.items ?? [];
  if (items.length === 0) return null;
  const headingId = `section-${index}-heading`;

  // A "note" section renders as a soft callout, not a heading + list.
  if (section.kind === "note") {
    return (
      <div
        role="note"
        className="rounded-xl border border-border bg-muted/50 px-3 py-2.5 text-sm text-foreground"
      >
        {section.heading && (
          <p className="mb-1 font-semibold">{section.heading}</p>
        )}
        <div className="space-y-1">
          {items.map((item, i) => (
            <p key={i} className="leading-relaxed">{item}</p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <section aria-labelledby={headingId} className="space-y-2">
      {section.heading && (
        <h3
          id={headingId}
          className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
        >
          {section.heading}
        </h3>
      )}
      {section.kind === "steps" ? (
        <ol className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                aria-hidden="true"
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary"
              >
                {i + 1}
              </span>
              <span className="text-sm leading-relaxed text-foreground">{item}</span>
            </li>
          ))}
        </ol>
      ) : (
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2">
              <span
                aria-hidden="true"
                className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-secondary"
              />
              <span className="text-sm leading-relaxed text-foreground">{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
