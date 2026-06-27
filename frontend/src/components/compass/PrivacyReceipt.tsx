import { ShieldCheck } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { PrivacyReceipt as PrivacyReceiptType } from "@/lib/types";

interface PrivacyReceiptProps {
  receipt: PrivacyReceiptType;
  id: string;
}

function storageLabel(storage: PrivacyReceiptType["storage"]): string {
  switch (storage) {
    case "local":
      return "Stored on your device only";
    case "session":
      return "Kept only for this session";
    case "none":
      return "Not stored anywhere";
  }
}

function FieldList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      {items.length === 0 ? (
        <p className="mt-1 text-sm text-muted-foreground">None</p>
      ) : (
        <ul className="mt-1 flex flex-wrap gap-1.5">
          {items.map((f) => (
            <li
              key={f}
              className="rounded-full border border-border bg-background px-2 py-0.5 text-xs text-foreground"
            >
              {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function PrivacyReceipt({ receipt, id }: PrivacyReceiptProps) {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem
        value={id}
        className="rounded-2xl border border-border bg-card/60 shadow-sm"
      >
        <AccordionTrigger className="px-4 py-3 text-sm hover:no-underline">
          <span className="flex items-center gap-2 text-start font-medium text-foreground">
            <ShieldCheck className="h-4 w-4 text-secondary" aria-hidden="true" />
            What data was used
          </span>
        </AccordionTrigger>
        <AccordionContent className="px-4 pb-4">
          <div className="space-y-3">
            <FieldList label="Used for this answer" items={receipt.used_fields} />
            <FieldList label="Saved for next steps" items={receipt.stored_fields} />
            <div className="flex items-center gap-2 rounded-xl bg-muted/60 px-3 py-2">
              <ShieldCheck
                className="h-4 w-4 text-success"
                aria-hidden="true"
              />
              <span className="text-sm text-foreground">
                {storageLabel(receipt.storage)}
              </span>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
