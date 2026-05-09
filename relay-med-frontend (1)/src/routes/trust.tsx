import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { ShieldCheck, Lock, EyeOff, UserCheck, FileLock2 } from "lucide-react";

export const Route = createFileRoute("/trust")({ component: Page });

const items = [
  { icon: Lock, t: "AES-256 Encryption", d: "All your data is encrypted at rest and in transit." },
  { icon: FileLock2, t: "Immutable Audit Trail", d: "Every access is logged and cryptographically signed." },
  { icon: EyeOff, t: "Zero Data Selling", d: "We never sell or share your data with third parties." },
  { icon: UserCheck, t: "Role-Based Access", d: "Only you and your authorized clinicians see your record." },
];

function Page() {
  return (
    <PageShell title="Trust Center" subtitle="Transparency about how your data flows, who sees it, and why." icon={ShieldCheck}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((i) => {
          const Icon = i.icon;
          return (
            <div key={i.t} className="rounded-2xl border bg-white p-5 flex items-start gap-4">
              <div className="w-11 h-11 rounded-xl bg-mint grid place-items-center text-sage"><Icon className="w-5 h-5" /></div>
              <div>
                <div className="font-display text-base font-semibold">{i.t}</div>
                <p className="text-sm text-muted-foreground mt-1">{i.d}</p>
              </div>
            </div>
          );
        })}
      </div>
    </PageShell>
  );
}
