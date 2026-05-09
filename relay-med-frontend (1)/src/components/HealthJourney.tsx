import { Moon, Footprints, Activity, Apple, Heart, RotateCw, Scale, HeartPulse, Waves, Flame, Battery, Zap, ShieldCheck, Bed, Smile, Info } from "lucide-react";

type Node = { id: string; label: string; sub: string; icon: any; trust?: number; tone?: "good" | "warn" | "bad" };

const inputs: Node[] = [
  { id: "sleep", label: "Sleep Quality", sub: "Good", icon: Moon, trust: 95, tone: "good" },
  { id: "activity", label: "Daily Activity", sub: "Moderate", icon: Footprints, trust: 92, tone: "good" },
  { id: "stress", label: "Stress Levels", sub: "Elevated", icon: Activity, trust: 78, tone: "bad" },
  { id: "nutrition", label: "Nutrition", sub: "Balanced", icon: Apple, trust: 88, tone: "good" },
  { id: "hr", label: "Heart Rate Trends", sub: "Normal", icon: Heart, trust: 94, tone: "good" },
  { id: "rec", label: "Recovery Consistency", sub: "Good", icon: RotateCw, trust: 91, tone: "good" },
];

const middle: Node[] = [
  { id: "weight", label: "Weight Stability", sub: "Improving", icon: Scale },
  { id: "bp", label: "Blood Pressure Balance", sub: "Balanced", icon: HeartPulse },
  { id: "cv", label: "Cardiovascular Load", sub: "Moderate", icon: Waves },
  { id: "meta", label: "Metabolic Stress", sub: "Normal", icon: Flame },
  { id: "cap", label: "Recovery Capacity", sub: "Good", icon: Battery },
];

const outputs: Node[] = [
  { id: "energy", label: "Improved Energy", sub: "High", icon: Zap },
  { id: "risk", label: "Lower Long-Term Risk", sub: "Improving", icon: ShieldCheck },
  { id: "heart", label: "Better Heart Health", sub: "On Track", icon: Heart },
  { id: "sleeprec", label: "Better Sleep Recovery", sub: "Improving", icon: Bed },
  { id: "stressred", label: "Reduced Stress Burden", sub: "Improving", icon: Smile },
];

// edges as relative percents in container — left col x≈22%, mid x≈52%, right x≈82%
const edges: { from: [number, number]; to: [number, number]; tone: "pos" | "neg" | "neu" }[] = [
  // inputs -> middle (6 inputs, 5 middle)
  { from: [0, 0], to: [1, 0], tone: "pos" }, // sleep -> weight
  { from: [0, 1], to: [1, 1], tone: "pos" }, // activity -> bp
  { from: [0, 2], to: [1, 2], tone: "neg" }, // stress -> cv
  { from: [0, 2], to: [1, 3], tone: "neg" }, // stress -> meta
  { from: [0, 3], to: [1, 0], tone: "pos" }, // nutrition -> weight
  { from: [0, 4], to: [1, 1], tone: "pos" },
  { from: [0, 4], to: [1, 2], tone: "pos" },
  { from: [0, 5], to: [1, 4], tone: "pos" },
  { from: [0, 1], to: [1, 3], tone: "pos" },
  // middle -> outputs (5 middle, 5 outputs)
  { from: [1, 0], to: [2, 0], tone: "pos" },
  { from: [1, 1], to: [2, 1], tone: "pos" },
  { from: [1, 2], to: [2, 2], tone: "pos" },
  { from: [1, 2], to: [2, 1], tone: "pos" },
  { from: [1, 3], to: [2, 2], tone: "neg" },
  { from: [1, 4], to: [2, 3], tone: "pos" },
  { from: [1, 4], to: [2, 4], tone: "pos" },
  { from: [1, 0], to: [2, 0], tone: "pos" },
  { from: [1, 1], to: [2, 2], tone: "pos" },
];

const colX = [16, 50, 84];
function rowsY(count: number) {
  // returns array of y percentages between 8 and 92
  return Array.from({ length: count }, (_, i) => 10 + (i * 80) / (count - 1));
}

function NodeChip({ n }: { n: Node }) {
  const Icon = n.icon;
  const toneRing =
    n.tone === "bad"
      ? "border-[color:color-mix(in_oklab,var(--coral)_40%,transparent)] bg-[color:color-mix(in_oklab,var(--coral)_8%,white)]"
      : n.tone === "warn"
        ? "border-[color:color-mix(in_oklab,var(--warning)_40%,transparent)] bg-[color:color-mix(in_oklab,var(--warning)_8%,white)]"
        : "border-[color:color-mix(in_oklab,var(--sage)_25%,transparent)] bg-white";
  return (
    <div className={`rounded-2xl border ${toneRing} px-3.5 py-2.5 shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5 backdrop-blur-sm`}>
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-xl bg-mint/70 grid place-items-center text-sage shrink-0">
          <Icon className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <div className="text-[12px] font-medium leading-tight truncate">{n.label}</div>
          <div className={`text-[10px] leading-tight ${n.tone === "bad" ? "text-[color:var(--coral)]" : "text-muted-foreground"}`}>{n.sub}</div>
        </div>
        {n.trust != null && (
          <div className="ml-auto text-[10px] font-semibold text-sage">{n.trust}%</div>
        )}
      </div>
    </div>
  );
}

export function HealthJourney() {
  const ys = [rowsY(inputs.length), rowsY(middle.length), rowsY(outputs.length)];
  const cols = [inputs, middle, outputs];

  return (
    <section className="soft-card p-6 fade-in">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-display font-semibold flex items-center gap-2">Your Health Journey <Info className="w-4 h-4 text-muted-foreground" /></h2>
          <p className="text-sm text-muted-foreground mt-1">AI-powered prediction of how daily habits shape future health.</p>
        </div>
        <button className="text-xs font-medium text-sage neu-btn px-3.5 py-2 rounded-xl">View Full Pathway</button>
      </div>

      <div className="grid grid-cols-3 text-[11px] font-medium text-muted-foreground mt-6 mb-2 px-2">
        <div>Your Habits & Inputs <span className="ml-2 text-sage">Trust Score</span></div>
        <div className="text-center">Key Health Factors</div>
        <div className="text-right">Future Outcomes</div>
      </div>

      <div className="relative w-full" style={{ height: 420 }}>
        {/* SVG edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none" viewBox="0 0 100 100">
          {edges.map((e, i) => {
            const [c1, r1] = e.from;
            const [c2, r2] = e.to;
            const x1 = colX[c1] + 6;
            const y1 = ys[c1][r1];
            const x2 = colX[c2] - 6;
            const y2 = ys[c2][r2];
            const cx = (x1 + x2) / 2;
            const stroke =
              e.tone === "pos" ? "oklch(0.62 0.12 160)" : e.tone === "neg" ? "oklch(0.72 0.16 30)" : "oklch(0.66 0.11 230)";
            return (
              <path
                key={i}
                d={`M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`}
                fill="none"
                stroke={stroke}
                strokeOpacity={0.5}
                strokeWidth={0.4}
                className="pathway-line"
                vectorEffect="non-scaling-stroke"
              />
            );
          })}
        </svg>

        {/* Node columns */}
        {cols.map((col, ci) => (
          <div key={ci} className="absolute" style={{ left: `${colX[ci]}%`, transform: "translateX(-50%)", top: 0, bottom: 0, width: "28%" }}>
            {col.map((n, ri) => (
              <div key={n.id} className="absolute left-0 right-0" style={{ top: `${ys[ci][ri]}%`, transform: "translateY(-50%)" }}>
                <NodeChip n={n} />
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-5 text-[11px] text-muted-foreground mt-4 pt-4 border-t">
        <span className="flex items-center gap-2"><span className="inline-block w-6 h-[2px] rounded" style={{ background: "oklch(0.62 0.12 160)" }} /> Positive Influence</span>
        <span className="flex items-center gap-2"><span className="inline-block w-6 h-[2px] rounded border-t border-dashed" style={{ borderColor: "oklch(0.72 0.16 30)" }} /> Negative Influence</span>
        <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-sage/40" /> Input</span>
        <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full" style={{ background: "color-mix(in oklab, var(--ocean) 40%, white)" }} /> Intermediate Factor</span>
        <span className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full" style={{ background: "color-mix(in oklab, var(--warning) 60%, white)" }} /> Outcome</span>
      </div>
    </section>
  );
}
