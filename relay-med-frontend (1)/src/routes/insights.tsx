import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { Sparkles, TrendingUp, AlertTriangle, Lightbulb } from "lucide-react";

export const Route = createFileRoute("/insights")({ component: Page });

const insights = [
  { icon: TrendingUp, title: "Cardiovascular load improving", body: "Your HRV has improved 9% over the last 14 days, suggesting better autonomic recovery.", tone: "good" },
  { icon: AlertTriangle, title: "Recurring evening stress spikes", body: "Stress consistently rises between 8–10pm. Consider a wind-down routine.", tone: "warn" },
  { icon: Lightbulb, title: "Sleep window optimization", body: "Falling asleep before 11:15pm correlates with +18% next-day recovery.", tone: "good" },
  { icon: TrendingUp, title: "Activity consistency streak", body: "5 days in a row above your daily activity goal. Keep it going!", tone: "good" },
];

function Page() {
  return (
    <PageShell title="Health Insights" subtitle="AI-derived patterns from your trusted health signals." icon={Sparkles}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((it) => {
          const Icon = it.icon;
          return (
            <div key={it.title} className="rounded-2xl border bg-white p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-xl grid place-items-center ${it.tone === "warn" ? "bg-[color:color-mix(in_oklab,var(--coral)_15%,white)] text-[color:var(--coral)]" : "bg-mint text-sage"}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-display text-base font-semibold">{it.title}</div>
                  <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{it.body}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </PageShell>
  );
}
