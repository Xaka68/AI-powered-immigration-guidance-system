import { FreeTextInput } from "./FreeTextInput";

interface WelcomeScreenProps {
  onSubmit: (text: string) => void;
}

export function WelcomeScreen({ onSubmit }: WelcomeScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-16">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-foreground">
          Hey, what do you need help with?
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Housing, registration, healthcare, work — I'll guide you step by step.
        </p>
      </div>
      <div className="w-full max-w-xl">
        <FreeTextInput label="Type your question" onSubmit={onSubmit} />
      </div>
    </div>
  );
}
