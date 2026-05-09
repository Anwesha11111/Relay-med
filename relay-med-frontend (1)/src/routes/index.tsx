import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/AppLayout";
import { MetricsRow } from "@/components/MetricsRow";
import { HealthJourney } from "@/components/HealthJourney";
import { RelayGuidePanel } from "@/components/RelayGuidePanel";
import { InsightGrid } from "@/components/InsightGrid";
import { SecurityFooter } from "@/components/SecurityFooter";

export const Route = createFileRoute("/")(
  {
    component: Dashboard,
    head: () => ({
      meta: [
        { title: "Relay-med · Your AI Health Companion" },
        { name: "description", content: "Trust-aware predictive healthcare intelligence — your personalized, explainable wellness dashboard." },
      ],
    }),
  }
);

function Dashboard() {
  return (
    <AppLayout greeting="" subtitle="Here's your personalized health outlook today.">
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-5">
        <div className="space-y-5 min-w-0">
          <MetricsRow />
          <HealthJourney />
          <InsightGrid />
        </div>
        <RelayGuidePanel />
      </div>
      <SecurityFooter />
    </AppLayout>
  );
}
