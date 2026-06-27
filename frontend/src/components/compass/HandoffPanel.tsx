import { useMemo, useState } from "react";
import { UserRound, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Session, StructuredAnswer } from "@/lib/types";

interface HandoffPanelProps {
  session: Session | null;
  answer: StructuredAnswer | null;
  assistantMessage: string;
  id: string;
}

function deriveSummary(
  session: Session | null,
  answer: StructuredAnswer | null,
  assistantMessage: string,
) {
  const goal =
    (session?.journey_id && session.journey_id.replaceAll("_", " ")) ||
    "Newly-arrived person seeking guidance in Germany.";
  const knownPairs = Object.entries(session?.slots ?? {})
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}: ${String(v)}`);
  const known = knownPairs.length
    ? knownPairs.join("\n")
    : "No personal details have been collected yet.";
  const open =
    answer?.uncertainty?.trim() ||
    answer?.short_answer?.trim() ||
    assistantMessage?.trim() ||
    "User would like help continuing this journey.";
  return { goal, known, open };
}

export function HandoffPanel({
  session,
  answer,
  assistantMessage,
  id,
}: HandoffPanelProps) {
  const initial = useMemo(
    () => deriveSummary(session, answer, assistantMessage),
    [session, answer, assistantMessage],
  );
  const [goal, setGoal] = useState(initial.goal);
  const [known, setKnown] = useState(initial.known);
  const [open, setOpen] = useState(initial.open);
  const [consent, setConsent] = useState(false);
  const [shared, setShared] = useState(false);

  return (
    <section
      aria-labelledby={`${id}-title`}
      className="space-y-4 rounded-2xl border-2 border-accent/40 bg-card p-5 shadow-sm"
    >
      <header className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 text-accent"
        >
          <UserRound className="h-5 w-5" />
        </span>
        <div>
          <h3
            id={`${id}-title`}
            className="font-display text-base font-semibold text-foreground"
          >
            Talk to a human counselor
          </h3>
          <p className="text-sm text-muted-foreground">
            Review and edit the summary below. Nothing is sent until you agree.
          </p>
        </div>
      </header>

      <div className="space-y-3">
        <div>
          <Label htmlFor={`${id}-goal`} className="text-sm font-medium">
            Your goal
          </Label>
          <Textarea
            id={`${id}-goal`}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            rows={2}
            className="mt-1 bg-background"
            disabled={shared}
          />
        </div>
        <div>
          <Label htmlFor={`${id}-known`} className="text-sm font-medium">
            What the counselor should know
          </Label>
          <Textarea
            id={`${id}-known`}
            value={known}
            onChange={(e) => setKnown(e.target.value)}
            rows={3}
            className="mt-1 bg-background"
            disabled={shared}
          />
        </div>
        <div>
          <Label htmlFor={`${id}-open`} className="text-sm font-medium">
            Open questions
          </Label>
          <Textarea
            id={`${id}-open`}
            value={open}
            onChange={(e) => setOpen(e.target.value)}
            rows={3}
            className="mt-1 bg-background"
            disabled={shared}
          />
        </div>
      </div>

      <div className="flex items-start gap-2 rounded-xl bg-muted/60 p-3">
        <Checkbox
          id={`${id}-consent`}
          checked={consent}
          onCheckedChange={(v) => setConsent(v === true)}
          disabled={shared}
          className="mt-0.5"
        />
        <Label
          htmlFor={`${id}-consent`}
          className="text-sm font-normal leading-relaxed"
        >
          I agree to share this summary with a counselor. My chat messages are
          not included.
        </Label>
      </div>

      <Button
        type="button"
        disabled={!consent || shared}
        onClick={() => setShared(true)}
        className="min-h-12 w-full gap-2 bg-accent text-accent-foreground hover:bg-accent/90"
      >
        <Send className="h-4 w-4" aria-hidden="true" />
        {shared ? "Summary ready to share" : "Share with counselor"}
      </Button>
      {shared && (
        <p className="text-center text-xs text-muted-foreground">
          Your summary is prepared. A counselor will contact you using the
          channel you choose.
        </p>
      )}
    </section>
  );
}
