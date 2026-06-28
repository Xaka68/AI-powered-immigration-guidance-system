import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Header } from "@/components/compass/Header";
import { ChatThread } from "@/components/compass/ChatThread";
import { OptionQuestionCard } from "@/components/compass/OptionQuestionCard";
import { FreeTextInput } from "@/components/compass/FreeTextInput";
import { WelcomeScreen } from "@/components/compass/WelcomeScreen";
import { useCompass } from "@/hooks/use-compass";
import { getStrings, isRTL } from "@/lib/translations";

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

const PAD = "w-full px-4 sm:px-8 lg:px-12";

function CompassPage() {
  const {
    turns,
    options,
    session,
    status,
    steps,
    selectOption,
    sendText,
    retry,
    startOver,
    setLanguage,
  } = useCompass();

  const lang = (session?.slots?.language as string) || "en";
  const strings = getStrings(lang);
  const rtl = isRTL(lang);

  // Keep <html dir> in sync whenever the detected language changes (e.g. auto-detect
  // on first message). The hook handles explicit switcher clicks; this covers auto.
  useEffect(() => {
    document.documentElement.dir = rtl ? "rtl" : "ltr";
    document.documentElement.lang = lang;
  }, [lang, rtl]);

  const busy = status === "loading";
  const isEmpty = turns.length === 0;

  const [optionsDismissed, setOptionsDismissed] = useState(false);
  useEffect(() => {
    setOptionsDismissed(false);
  }, [options]);

  const showOptions = options.length > 0 && !optionsDismissed && !busy;

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <Header
        session={session}
        onStartOver={startOver}
        onSetLanguage={setLanguage}
        startOverLabel={strings.start_over}
        privacyTagline={strings.privacy_tagline}
      />

      <main className={`${PAD} flex flex-1 flex-col pt-2 pb-4`}>
        {isEmpty ? (
          <WelcomeScreen onSubmit={sendText} strings={strings} />
        ) : (
          <div className="space-y-4 pb-36">
            <ChatThread
              turns={turns}
              status={status}
              session={session}
              steps={steps}
              onRetry={retry}
            />
            {showOptions && (
              <OptionQuestionCard
                options={options}
                disabled={busy}
                onSelect={selectOption}
                onSubmitText={sendText}
                onSkip={() => setOptionsDismissed(true)}
                orTypeItLabel={strings.or_type_it}
                skipLabel={strings.skip}
              />
            )}
          </div>
        )}
      </main>

      {!isEmpty && (
        <div className="sticky bottom-0 z-10 border-t border-border bg-background/90 backdrop-blur">
          <div className={`${PAD} flex flex-col gap-3 py-3`}>
            <FreeTextInput
              disabled={busy}
              placeholder={
                showOptions
                  ? strings.input_placeholder_options
                  : strings.input_placeholder
              }
              onSubmit={sendText}
            />
          </div>
        </div>
      )}
    </div>
  );
}
