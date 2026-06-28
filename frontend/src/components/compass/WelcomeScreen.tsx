import { FreeTextInput } from "./FreeTextInput";
import { LogoMark } from "./LogoMark";
import type { Strings } from "@/lib/translations";

interface WelcomeScreenProps {
  onSubmit: (text: string) => void;
  strings: Strings;
}

export function WelcomeScreen({ onSubmit, strings }: WelcomeScreenProps) {
  const quickStarts = [
    { label: strings.qs_register_label, prompt: strings.qs_register_prompt },
    { label: strings.qs_housing_label, prompt: strings.qs_housing_prompt },
    { label: strings.qs_german_label, prompt: strings.qs_german_prompt },
    { label: strings.qs_health_label, prompt: strings.qs_health_prompt },
  ];

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
            {strings.welcome_heading}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground whitespace-pre-line">
            {strings.welcome_subtitle}
          </p>
        </div>
      </div>

      <div className="grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
        {quickStarts.map((qs) => (
          <button
            key={qs.label}
            type="button"
            onClick={() => onSubmit(qs.prompt)}
            className="rounded-xl border border-border bg-card px-4 py-2.5 text-start text-sm font-medium text-foreground transition-colors hover:border-foreground/30 hover:bg-muted active:scale-[0.98]"
          >
            {qs.label}
          </button>
        ))}
      </div>

      <div className="w-full max-w-2xl">
        <FreeTextInput
          label={strings.input_label}
          placeholder={strings.input_placeholder}
          onSubmit={onSubmit}
        />
      </div>
    </div>
  );
}
