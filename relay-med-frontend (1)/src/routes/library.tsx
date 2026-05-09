import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { BookOpen } from "lucide-react";

export const Route = createFileRoute("/library")({ component: Page });

const articles = [
  { t: "Understanding Heart Rate Variability", c: "Cardio", min: 4 },
  { t: "Sleep Architecture & Recovery", c: "Sleep", min: 6 },
  { t: "Causal Inference in Personal Health", c: "AI", min: 8 },
  { t: "Stress, Cortisol, and Long-Term Risk", c: "Wellness", min: 5 },
  { t: "Trust-Aware Health Data Explained", c: "Trust", min: 3 },
  { t: "Building Sustainable Lifestyle Habits", c: "Habits", min: 7 },
];

function Page() {
  return (
    <PageShell title="Health Library" subtitle="Curated, evidence-based reads to deepen your wellness journey." icon={BookOpen}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {articles.map((a) => (
          <div key={a.t} className="rounded-2xl border bg-white p-5 hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-[10px] uppercase tracking-wider text-sage font-semibold">{a.c}</div>
            <div className="font-display text-base font-semibold mt-1">{a.t}</div>
            <div className="text-xs text-muted-foreground mt-2">{a.min} min read</div>
          </div>
        ))}
      </div>
    </PageShell>
  );
}
