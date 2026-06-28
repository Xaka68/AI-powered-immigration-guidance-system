import { FreeTextInput } from "./FreeTextInput";
import { LogoMark } from "./LogoMark";

const QUICK_STARTS = [
  { label: "Register my address", prompt: "How do I register my address in Germany?" },
  { label: "Find housing", prompt: "How can I find an apartment as a newcomer in Germany?" },
  { label: "Learn German", prompt: "Where can I take a free German language course?" },
  { label: "Get health insurance", prompt: "How do I get health insurance in Germany?" },
];

interface WelcomeScreenProps {
  onSubmit: (text: string) => void;
}

export function WelcomeScreen({ onSubmit }: WelcomeScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-12">
      <div className="flex flex-col items-center gap-4 text-center">
        <span
          aria-hidden="true"
          className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground"
        >
          <LogoMark className="h-7 w-7" />
        </span>
        <div>
          <h2 className="font-display text-2xl font-semibold text-foreground">
            How can I help you?
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Your guide to life in Germany — housing, registration, health, courses.
            <br />
            Your data stays on this device.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-2">
        {QUICK_STARTS.map((qs) => (
          <button
            key={qs.label}
            type="button"
            onClick={() => onSubmit(qs.prompt)}
            className="rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-muted active:scale-[0.98]"
          >
            {qs.label}
          </button>
        ))}
      </div>

      <div className="w-full max-w-2xl">
        <FreeTextInput label="Or type your question" onSubmit={onSubmit} />
      </div>
    </div>
  );
}
