import { Loader2, Mic, Paperclip, Plus, Send, Square, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { transcribeAudio } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Attachment } from "@/lib/types";

interface FreeTextInputProps {
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  onSubmit: (text: string, attachment?: Attachment) => void;
}

export function FreeTextInput({ disabled, label, placeholder, onSubmit }: FreeTextInputProps) {
  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [attached, setAttached] = useState<Attachment | null>(null);
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
    if (!trimmed && !attached) return;
    onSubmit(trimmed, attached ?? undefined);
    setValue("");
    setAttached(null);
  }

  // ── Voice: record → transcribe (OpenAI STT) → fill the input ──────────────────
  async function startRecording() {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Pick the best supported format — opus/webm is preferred, mp4 for Safari.
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/mp4")
          ? "audio/mp4"
          : "";
      const mr = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      // Timeslice of 250ms ensures chunks are collected even on short recordings.
      mr.ondataavailable = (e) => {
        if (e.data.size) chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mr.mimeType || "audio/webm" });
        if (!blob.size) {
          setMicError("No audio captured — try again.");
          return;
        }
        setTranscribing(true);
        try {
          const text = await transcribeAudio(blob);
          if (text) setValue((v) => (v ? `${v} ${text}` : text));
          inputRef.current?.focus();
        } catch (err) {
          console.error(err);
          setMicError("Transcription failed — please type instead.");
        } finally {
          setTranscribing(false);
        }
      };
      recorderRef.current = mr;
      mr.start(250);
      setRecording(true);
    } catch (err) {
      console.error("microphone unavailable", err);
      setMicError("Microphone unavailable — check browser permissions.");
    }
  }

  function toggleMic() {
    if (recording) recorderRef.current?.stop();
    else void startRecording();
  }

  function onFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    e.target.value = "";

    const reader = new FileReader();
    if (f.type.startsWith("image/")) {
      reader.onload = () => {
        const dataUrl = reader.result as string;
        // strip the "data:<mime>;base64," prefix
        const base64 = dataUrl.split(",")[1] ?? "";
        setAttached({ name: f.name, mime_type: f.type, base64 });
      };
      reader.readAsDataURL(f);
    } else {
      reader.onload = () => {
        setAttached({ name: f.name, mime_type: f.type || "text/plain", text: reader.result as string });
      };
      reader.readAsText(f);
    }
  }

  const busy = disabled || transcribing;

  return (
    <form onSubmit={handle} className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor="compass-free-text" className="text-xs font-medium text-muted-foreground">
          {label}
        </label>
      )}

      {/* Attachment chip */}
      {attached && (
        <div className="flex w-fit items-center gap-2 rounded-full bg-muted px-3 py-1 text-xs text-foreground">
          <Paperclip className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
          <span className="max-w-[14rem] truncate">{attached.name}</span>
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
          disabled={busy || (!value.trim() && !attached)}
          aria-label="Send message"
          className="absolute end-2 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {micError && (
        <p className="px-2 text-xs text-destructive">{micError}</p>
      )}
    </form>
  );
}
