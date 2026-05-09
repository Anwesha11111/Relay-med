import { AppLayout } from "./AppLayout";
import { SecurityFooter } from "./SecurityFooter";
import type { LucideIcon } from "lucide-react";

export function PageShell({
  title,
  subtitle,
  icon: Icon,
  children,
}: {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  children: React.ReactNode;
}) {
  return (
    <AppLayout greeting={title} subtitle={subtitle}>
      <div className="soft-card p-6 fade-in">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-2xl gradient-sage grid place-items-center text-white">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold">{title}</h2>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
        </div>
        {children}
      </div>
      <SecurityFooter />
    </AppLayout>
  );
}
