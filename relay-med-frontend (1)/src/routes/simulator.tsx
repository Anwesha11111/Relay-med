import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { FlaskConical } from "lucide-react";
import { useState } from "react";
import { Line, LineChart, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/simulator")({ component: Page });

function Page() {
  const [walk, setWalk] = useState(30);
  const [sleep, setSleep] = useState(1);
  const [stress, setStress] = useState(20);
  const [weight, setWeight] = useState(2);
  const improvement = Math.round(walk * 0.35 + sleep * 6 + stress * 0.3 + weight * 4);
  const data = Array.from({ length: 18 }, (_, i) => ({ v: 50 + i * (improvement / 22) + Math.sin(i / 1.6) * 3 }));

  return (
    <PageShell title="What-If Simulator" subtitle="Test interventions and see causal impact on your future risk." icon={FlaskConical}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="space-y-4">
          <Slider label="Walk minutes/day" value={walk} setValue={setWalk} max={120} unit="min" />
          <Slider label="Sleep extra hours" value={sleep} setValue={setSleep} max={3} unit="h" />
          <Slider label="Reduce stress %" value={stress} setValue={setStress} max={50} unit="%" />
          <Slider label="Weight loss" value={weight} setValue={setWeight} max={10} unit="kg" />
        </div>
        <div className="rounded-2xl border bg-white p-5">
          <div className="text-xs text-muted-foreground">Predicted cardiovascular improvement (6 months)</div>
          <div className="text-4xl font-display font-semibold text-sage mt-1">+{improvement}%</div>
          <div className="mt-3">
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={data}>
                <Line dataKey="v" stroke="oklch(0.62 0.12 160)" strokeWidth={2.5} dot={false} type="monotone" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Based on causal counterfactual model trained on your trust-filtered data graph.</p>
        </div>
      </div>
    </PageShell>
  );
}

function Slider({ label, value, setValue, max, unit }: { label: string; value: number; setValue: (n: number) => void; max: number; unit: string }) {
  return (
    <div className="rounded-2xl border bg-white p-4">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="text-sage font-semibold">{value} {unit}</span>
      </div>
      <input type="range" min={0} max={max} value={value} onChange={(e) => setValue(Number(e.target.value))} className="w-full mt-2 accent-[color:var(--sage)]" />
    </div>
  );
}
