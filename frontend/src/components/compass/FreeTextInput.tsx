import { Loader2, Mic, Paperclip, Plus, Send, Square, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { transcribeAudio } from "@/lib/api";
import { cn } from "@/lib/utils";

interface FreeTextInputProps {
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  onSubmit: (text: string) => void;
}

export function FreeTextInput({ disabled, label, placeholder, onSubmit }: FreeTextInputProps) {
  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [attached, setAttached] = useState<string | null>(null); // demo only
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const prevDisabledRef = useRef(disabled);

  // Auto-focus when the loading state clears (disabled true → false).
  useEffect(() => {
    if (prevDisabledRef.current && !disabled) inputRef.current?.focus();
    prevDisabledRef.current = disabled;
  }, [disabled]);

  function handle(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  }

  // ── Voice: record → transcribe (OpenAI STT) → fill the input ──────────────────
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mr.mimeType || "audio/webm" });
        if (!blob.size) return;
        setTranscribing(true);
        try {
          const text = await transcribeAudio(blob);
          if (text) setValue((v) => (v ? `${v} ${text}` : text));
          inputRef.current?.focus();
        } catch (err) {
          console.error(err);
        } finally {
          setTranscribing(false);
        }
      };
      recorderRef.current = mr;
      mr.start();
      setRecording(true);
    } catch (err) {
      console.error("microphone unavailable", err);
    }
  }

  function toggleMic() {
    if (recording) recorderRef.current?.stop();
    else void startRecording();
  }

  function onFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setAttached(f.name); // demo only — not uploaded or read by the model
    e.target.value = "";
  }

  const busy = disabled || transcribing;

  return (
    <form onSubmit={handle} className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor="compass-free-text" className="text-xs font-medium text-muted-foreground">
          {label}
        </label>
      )}

      {/* Attachment chip (demo: shown but not sent to the model) */}
      {attached && (
        <div className="flex w-fit items-center gap-2 rounded-full bg-muted px-3 py-1 text-xs text-foreground">
          <Paperclip className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
          <span className="max-w-[14rem] truncate">{attached}</span>
          <button
            type="button"
            aria-label="Remove attachment"
            onClick={() => setAttached(null)}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      <div className="relative flex items-center">
        {/* "+" attach (left) — demo only */}
        <input ref={fileRef} type="file" className="hidden" onChange={onFilePicked} />
        <button
          type="button"
          disabled={disabled}
          aria-label="Attach a file"
          onClick={() => fileRef.current?.click()}
          className="absolute start-2 flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Plus className="h-5 w-5" aria-hidden="true" />
        </button>

        <input
          ref={inputRef}
          id="compass-free-text"
          type="text"
          inputMode="text"
          autoComplete="off"
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          placeholder={
            recording
              ? "Listening…"
              : transcribing
                ? "Transcribing…"
                : placeholder ?? "Ask in your own words…"
          }
          className="w-full rounded-full border border-foreground/25 bg-card py-3 ps-12 pe-[5.5rem] text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        />

        {/* Mic (right, next to send) */}
        <button
          type="button"
          disabled={disabled || transcribing}
          aria-label={recording ? "Stop recording" : "Record voice"}
          aria-pressed={recording}
          onClick={toggleMic}
          className={cn(
            "absolute end-12 flex h-9 w-9 items-center justify-center rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-40",
            recording
              ? "bg-destructive text-destructive-foreground animate-pulse"
              : "text-muted-foreground hover:bg-muted hover:text-foreground",
          )}
        >
          {transcribing ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : recording ? (
            <Square className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <Mic className="h-4 w-4" aria-hidden="true" />
          )}
        </button>

        {/* Send */}
        <button
          type="submit"
          disabled={busy || !value.trim()}
          aria-label="Send message"
          className="absolute end-2 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </form>
  );
}
