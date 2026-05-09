import { Lock, ShieldCheck, EyeOff, UserCheck } from "lucide-react";

export function SecurityFooter() {
  const items = [
    { icon: Lock, text: "AES-256 Encrypted" },
    { icon: ShieldCheck, text: "No Data Selling" },
    { icon: EyeOff, text: "Privacy Preserved" },
    { icon: UserCheck, text: "You Control Your Data" },
  ];
  return (
    <footer className="soft-card mt-6 p-4 flex flex-wrap items-center justify-around gap-4 fade-in">
      <div className="text-xs text-muted-foreground">Your data is private, secure, and always under your control.</div>
      <div className="flex flex-wrap items-center gap-5">
        {items.map(({ icon: Icon, text }) => (
          <div key={text} className="flex items-center gap-2 text-xs text-foreground/70">
            <Icon className="w-3.5 h-3.5 text-sage" /> {text}
          </div>
        ))}
      </div>
    </footer>
  );
}
