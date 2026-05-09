import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { GitBranch } from "lucide-react";
import { HealthJourney } from "@/components/HealthJourney";

export const Route = createFileRoute("/causal-pathways")({ component: Page });

function Page() {
  return (
    <PageShell title="Causal Pathways" subtitle="See how lifestyle factors causally shape your future outcomes." icon={GitBranch}>
      <HealthJourney />
      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { t: "Root Cause", d: "Sedentary lifestyle → ↑ BMI → ↑ Hypertension" },
          { t: "Counterfactual", d: "If activity ↑ 20% → cardio risk ↓ 14%" },
          { t: "Filter", d: "Spurious correlation removed: caffeine ↔ stress" },
        ].map((c) => (
          <div key={c.t} className="rounded-2xl border bg-white p-4">
            <div className="text-xs text-muted-foreground">{c.t}</div>
            <div className="font-display text-base font-semibold mt-1">{c.d}</div>
          </div>
        ))}
      </div>
    </PageShell>
  );
}
