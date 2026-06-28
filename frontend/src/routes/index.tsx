import { createFileRoute } from "@tanstack/react-router";
import { Header } from "@/components/compass/Header";
import { ChatThread } from "@/components/compass/ChatThread";
import { OptionChips } from "@/components/compass/OptionChips";
import { FreeTextInput } from "@/components/compass/FreeTextInput";
import { WelcomeScreen } from "@/components/compass/WelcomeScreen";
import { useCompass } from "@/hooks/use-compass";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Integreat Compass" },
      {
        name: "description",
        content:
          "Calm, trusted, source-grounded guidance for newly-arrived migrants and refugees in Germany. Your data stays on your device.",
      },
      { property: "og:title", content: "Integreat Compass" },
      {
        property: "og:description",
        content:
          "Calm, trusted, source-grounded guidance for newly-arrived migrants and refugees in Germany.",
      },
    ],
  }),
  component: CompassPage,
});

// Fluid — expands to fill available screen width with breathing room on edges.
const PAD = "w-full px-4 sm:px-8 lg:px-12";

function CompassPage() {
  const {
    turns,
    options,
    session,
    status,
    selectOption,
    sendText,
    retry,
    startOver,
  } = useCompass();

  const busy = status === "loading";
  const isEmpty = turns.length === 0;

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <Header session={session} onStartOver={startOver} />

      <main className={`${PAD} flex flex-1 flex-col pt-2 pb-4`}>
        {isEmpty ? (
          <WelcomeScreen onSubmit={sendText} />
        ) : (
          <div className="pb-36">
            <ChatThread
              turns={turns}
              status={status}
              session={session}
              onRetry={retry}
            />
          </div>
        )}
      </main>

      {!isEmpty && (
        <div className="sticky bottom-0 z-10 border-t border-border bg-background/90 backdrop-blur">
          <div className={`${PAD} flex flex-col gap-3 py-3`}>
            {options.length > 0 && (
              <OptionChips
                options={options}
                disabled={busy}
                onSelect={selectOption}
              />
            )}
            <FreeTextInput disabled={busy} onSubmit={sendText} />
          </div>
        </div>
      )}
    </div>
  );
}
