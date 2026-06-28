import {
  CheckSquare,
  ChevronDown,
  Info,
  List,
  ListChecks,
  Mail,
  Map,
  MapPin,
  Phone,
  ShieldAlert,
  Square,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import type { AnswerSection, Source, StructuredAnswer } from "@/lib/types";
import { cn } from "@/lib/utils";
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

      {answer.uncertainty && <Limitations text={answer.uncertainty} />}

      <SourcesPopup sources={sources} />
    </article>
  );
}

// ── Section heading with an icon for scannability ──────────────────────────────────

function Heading({ id, icon: Icon, children }: { id: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <h3
      id={id}
      className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {children}
    </h3>
  );
}

function SectionBlock({ section, index }: { section: AnswerSection; index: number }) {
  const items = section.items ?? [];
  if (items.length === 0) return null;
  const headingId = `section-${index}-heading`;
  const kind = (section.kind || "list").toLowerCase();

  if (kind === "contact") return <ContactCard section={section} />;
  if (kind === "note") return <NoteCallout section={section} />;

  return (
    <section aria-labelledby={headingId} className="space-y-2">
      {section.heading && (
        <Heading
          id={headingId}
          icon={kind === "steps" ? ListChecks : kind === "checklist" ? CheckSquare : List}
        >
          {section.heading}
        </Heading>
      )}
      {kind === "steps" ? (
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
      ) : kind === "checklist" ? (
        <Checklist items={items} groupKey={section.heading || `c${index}`} />
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

// ── Contact card: office/address as text + tap-to-call / email / maps ──────────────

const EMAIL_RE = /[\w.+-]+@[\w-]+\.[\w.-]+/;
const PHONE_RE = /(\+?\d[\d\s()/\-]{5,}\d)/;
const POSTAL_RE = /\b\d{5}\b/;

function ContactCard({ section }: { section: AnswerSection }) {
  const text = (section.items ?? []).join("  ");
  const email = text.match(EMAIL_RE)?.[0];
  // Phone: prefer one labelled "phone/tel", else the first phone-like run.
  const phone =
    text.match(/(?:phone|tel|telefon)[^\d+]*(\+?\d[\d\s()/\-]{5,}\d)/i)?.[1] ||
    text.match(PHONE_RE)?.[0];
  const addressLine = (section.items ?? []).find((l) => POSTAL_RE.test(l));

  return (
    <section className="space-y-2 rounded-xl border border-border bg-muted/40 px-3.5 py-3">
      {section.heading && (
        <Heading id="contact-heading" icon={MapPin}>{section.heading}</Heading>
      )}
      <div className="space-y-0.5 text-sm leading-relaxed text-foreground">
        {(section.items ?? []).map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
      {(phone || email || addressLine) && (
        <div className="flex flex-wrap gap-2 pt-1">
          {phone && (
            <ContactButton href={`tel:${phone.replace(/[^\d+]/g, "")}`} icon={Phone}>
              Call
            </ContactButton>
          )}
          {email && (
            <ContactButton href={`mailto:${email}`} icon={Mail}>
              Email
            </ContactButton>
          )}
          {addressLine && (
            <ContactButton
              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addressLine)}`}
              icon={Map}
            >
              Open in Maps
            </ContactButton>
          )}
        </div>
      )}
    </section>
  );
}

function ContactButton({
  href,
  icon: Icon,
  children,
}: {
  href: string;
  icon: LucideIcon;
  children: React.ReactNode;
}) {
  const external = href.startsWith("http");
  return (
    <a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted"
    >
      <Icon className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
      {children}
    </a>
  );
}

// ── Note / safety callout (amber when it's a safety/important note) ────────────────

function NoteCallout({ section }: { section: AnswerSection }) {
  const safety = /safety|important|careful|warning|protect|danger|risk/i.test(
    section.heading || "",
  );
  return (
    <div
      role="note"
      className={cn(
        "rounded-xl border px-3.5 py-2.5 text-sm text-foreground",
        safety ? "border-warning/40 bg-warning/10" : "border-border bg-muted/50",
      )}
    >
      <p className="mb-1 flex items-center gap-1.5 font-semibold">
        {safety ? (
          <ShieldAlert className="h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
        ) : (
          <Info className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        )}
        {section.heading || "Good to know"}
      </p>
      <div className="space-y-1 ps-6">
        {(section.items ?? []).map((item, i) => (
          <p key={i} className="leading-relaxed">{item}</p>
        ))}
      </div>
    </div>
  );
}

// ── Tickable, device-persisted checklist (the "what do I still need" win) ──────────

const STORE_KEY = "compass_checklist";

function loadChecks(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY) || "{}");
  } catch {
    return {};
  }
}

function Checklist({ items, groupKey }: { items: string[]; groupKey: string }) {
  const [checks, setChecks] = useState<Record<string, boolean>>(() => loadChecks());

  const toggle = (item: string) => {
    const key = `${groupKey}::${item}`;
    const next = { ...checks, [key]: !checks[key] };
    setChecks(next);
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(next));
    } catch {
      /* storage disabled — ticks just won't persist */
    }
  };

  return (
    <ul className="space-y-1">
      {items.map((item, i) => {
        const checked = !!checks[`${groupKey}::${item}`];
        return (
          <li key={i}>
            <button
              type="button"
              onClick={() => toggle(item)}
              aria-pressed={checked}
              className="flex w-full items-start gap-2.5 rounded-lg px-1.5 py-1 text-start transition-colors hover:bg-muted/60"
            >
              {checked ? (
                <CheckSquare className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              ) : (
                <Square className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              )}
              <span
                className={cn(
                  "text-sm leading-relaxed",
                  checked ? "text-muted-foreground line-through" : "text-foreground",
                )}
              >
                {item}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// ── "What we couldn't confirm" — honest, but quiet and collapsed ───────────────────

function Limitations({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-border bg-muted/30 text-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-1.5 px-3.5 py-2 text-start text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <Info className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        What we couldn&apos;t confirm
        <ChevronDown
          className={cn("ms-auto h-4 w-4 transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <p className="border-t border-border px-3.5 py-2.5 leading-relaxed text-foreground">
          {text}
        </p>
      )}
    </div>
  );
}
