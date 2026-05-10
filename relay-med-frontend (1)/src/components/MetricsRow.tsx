import { Area, AreaChart, ResponsiveContainer, Line, LineChart } from "recharts";
import { Activity, Heart, Shield, Target, TrendingDown, TrendingUp, Moon, Droplet, Footprints, Flame } from "lucide-react";

const upTrend = Array.from({ length: 14 }, (_, i) => ({ v: 60 + Math.sin(i / 2) * 8 + i * 1.2 }));
const stableTrend = Array.from({ length: 14 }, (_, i) => ({ v: 70 + Math.sin(i / 1.5) * 5 }));
const downTrend = Array.from({ length: 14 }, (_, i) => ({ v: 80 - i * 1.2 + Math.sin(i / 1.5) * 4 }));

function Spark({ data, color }: { data: { v: number }[]; color: string }) {
  return (
    <ResponsiveContainer width="100%" height={50}>
      <AreaChart data={data} margin={{ top: 4, bottom: 0, left: 0, right: 0 }}>
        <defs>
          <linearGradient id={`g-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.4} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#g-${color})`} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MetricsRow() {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 fade-in">
      {/* Wellness Score */}
      <div className="soft-card p-5">
        <div className="flex items-start gap-4">
          <div className="relative w-[72px] h-[72px]">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle cx="18" cy="18" r="15.9155" fill="none" stroke="oklch(0.94 0.04 165)" strokeWidth="3" />
              <circle cx="18" cy="18" r="15.9155" fill="none" stroke="oklch(0.62 0.12 160)" strokeWidth="3" strokeLinecap="round" strokeDasharray="82, 100" />
            </svg>
            <Heart className="absolute inset-0 m-auto w-6 h-6 text-sage" />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Wellness Score</div>
            <div className="text-3xl font-display font-semibold leading-none mt-1">82<span className="text-sm text-muted-foreground font-sans">/100</span></div>
            <div className="flex items-center gap-1 text-xs mt-1.5 text-sage"><TrendingUp className="w-3 h-3" /> 6% this month</div>
          </div>
        </div>
        <p className="text-[11px] text-muted-foreground mt-3">Great job! Keep going.</p>
      </div>

      {/* Predicted Stability */}
      <div className="soft-card p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><div className="w-7 h-7 rounded-xl grid place-items-center" style={{ background: "color-mix(in oklab, var(--ocean) 18%, transparent)" }}><Shield className="w-4 h-4" style={{ color: "var(--ocean)" }} /></div>Predicted Health Stability</div>
            <div className="text-2xl font-display font-semibold mt-2">Stable</div>
            <div className="text-[11px] text-muted-foreground">Next 6 months outlook</div>
          </div>
        </div>
        <div className="mt-2 -mx-2"><Spark data={stableTrend} color="oklch(0.66 0.11 230)" /></div>
      </div>

      {/* Risk Change */}
      <div className="soft-card p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><div className="w-7 h-7 rounded-xl grid place-items-center" style={{ background: "color-mix(in oklab, var(--coral) 18%, transparent)" }}><Heart className="w-4 h-4" style={{ color: "var(--coral)" }} /></div>Risk Change</div>
            <div className="flex items-baseline gap-1 mt-2">
              <TrendingDown className="w-4 h-4" style={{ color: "var(--coral)" }} />
              <div className="text-2xl font-display font-semibold" style={{ color: "var(--coral)" }}>12%</div>
            </div>
            <div className="text-[11px] text-muted-foreground">Cardiovascular Risk · improved vs last month</div>
          </div>
        </div>
        <div className="mt-2 -mx-2"><Spark data={downTrend} color="oklch(0.72 0.16 30)" /></div>
      </div>

      {/* Active Goals */}
      <div className="soft-card p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground"><div className="w-7 h-7 rounded-xl grid place-items-center bg-mint"><Target className="w-4 h-4 text-sage" /></div>Active Goals</div>
            <div className="text-3xl font-display font-semibold mt-2">4</div>
            <div className="text-[11px] text-muted-foreground">in progress</div>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          {[Footprints, Moon, Droplet, Flame].map((I, i) => (
            <div key={i} onClick={() => alert("Goal tracking is coming in the next update!")} className="w-9 h-9 rounded-xl bg-mint/70 grid place-items-center text-sage hover:scale-110 transition-transform cursor-pointer">
              <I className="w-4 h-4" />
            </div>
          ))}
          <div onClick={() => alert("Goal tracking is coming in the next update!")} className="w-9 h-9 rounded-xl bg-mint/40 grid place-items-center text-[10px] text-sage font-semibold cursor-pointer">+1</div>
        </div>
      </div>
    </section>
  );
}
