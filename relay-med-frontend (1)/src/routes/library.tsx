import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { BookOpen, ChevronDown } from "lucide-react";

export const Route = createFileRoute("/library")({ component: Page });

const articles = [
  { t: "Understanding Heart Rate Variability", c: "Cardio", min: 4, desc: "Heart rate variability (HRV) is a measure of the variation in time between each heartbeat. It's a key indicator of your autonomic nervous system's balance and overall cardiovascular health." },
  { t: "Sleep Architecture & Recovery", c: "Sleep", min: 6, desc: "Learn about the different stages of sleep (REM, Deep, Light) and how they contribute to physical recovery, memory consolidation, and hormonal balance." },
  { t: "Causal Inference in Personal Health", c: "AI", min: 8, desc: "An overview of how Relay-med uses advanced causal AI to determine not just what is happening in your body, but *why* it's happening, cutting through random noise." },
  { t: "Stress, Cortisol, and Long-Term Risk", c: "Wellness", min: 5, desc: "Chronic stress leads to elevated cortisol levels, which can impact your immune system, weight, and cardiovascular health. Discover actionable ways to mitigate stress." },
  { t: "Trust-Aware Health Data Explained", c: "Trust", min: 3, desc: "How Relay-med weighs your data sources for accuracy. We prioritize clinically validated measurements over raw estimates to ensure your insights are trustworthy." },
  { t: "Building Sustainable Lifestyle Habits", c: "Habits", min: 7, desc: "Consistency beats intensity. Explore evidence-based psychological frameworks for building daily health habits that stick over the long term." },
];

function Page() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <PageShell title="Health Library" subtitle="Curated, evidence-based reads to deepen your wellness journey." icon={BookOpen}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {articles.map((a) => (
          <div key={a.t} onClick={() => setSelected(selected === a.t ? null : a.t)} className="rounded-2xl border bg-white p-5 hover:shadow-md transition-shadow cursor-pointer">
            <div className="flex justify-between items-start">
              <div className="text-[10px] uppercase tracking-wider text-sage font-semibold">{a.c}</div>
              <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${selected === a.t ? "rotate-180" : ""}`} />
            </div>
            <div className="font-display text-base font-semibold mt-1">{a.t}</div>
            {selected === a.t && (
              <div className="text-xs text-foreground/80 mt-3 leading-relaxed border-t pt-3">
                {a.desc}
              </div>
            )}
            <div className="text-xs text-muted-foreground mt-3">{a.min} min read</div>
          </div>
        ))}
      </div>
    </PageShell>
  );
}
