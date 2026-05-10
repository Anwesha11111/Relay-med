import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Area, AreaChart, ResponsiveContainer, Line, LineChart } from "recharts";
import { CalendarDays, ChevronDown, Moon, Activity, Droplet, HeartPulse, Watch, PenLine, Bed, Sparkles, Info, ArrowUpRight } from "lucide-react";

const horizons = [
  { label: "3 Months", status: "Low Risk", tag: "On Track", tone: "good" },
  { label: "6 Months", status: "Improving", tag: "Positive Trend", tone: "good" },
  { label: "12 Months", status: "Monitor Stress", tag: "Keep Consistent", tone: "warn" },
];

const insights = [
  { icon: Moon, text: "Sleep consistency improved by 14% this week.", tone: "good" },
  { icon: Activity, text: "Elevated stress detected on 3 days.", tone: "warn" },
  { icon: HeartPulse, text: "Recovery trending upward.", tone: "good" },
  { icon: Droplet, text: "Hydration is lower than usual. Drink more water!", tone: "warn" },
];

const trust = [
  { icon: Watch, label: "Wearable Sync", note: "98% trusted", val: 98, tone: "good" },
  { icon: PenLine, label: "Manual Entries", note: "Moderate confidence", val: 64, tone: "warn" },
  { icon: Bed, label: "Sleep Data", note: "Verified", val: 92, tone: "good" },
  { icon: HeartPulse, label: "Heart Rate Data", note: "High confidence", val: 88, tone: "good" },
];

const forecastData = Array.from({ length: 16 }, (_, i) => ({ v: 50 + i * 1.2 + Math.sin(i / 1.5) * 4 }));

export function InsightGrid() {
  const [walk, setWalk] = useState(30);
  const [sleep, setSleep] = useState(1);
  const [stress, setStress] = useState(20);
  const improvement = Math.round(walk * 0.35 + sleep * 6 + stress * 0.3);

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 fade-in">
      {/* Health Outlook */}
      <div className="soft-card p-5">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-lg font-semibold flex items-center gap-2">Health Outlook <Info className="w-3.5 h-3.5 text-muted-foreground" /></h3>
        </div>
        <div className="mt-4 space-y-3">
          {horizons.map((h) => (
            <div key={h.label} className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-mint/70 grid place-items-center text-sage"><CalendarDays className="w-4 h-4" /></div>
              <div className="flex-1">
                <div className="text-xs text-muted-foreground">{h.label}</div>
                <div className="text-sm font-medium">{h.status}</div>
              </div>
              <span className={`text-[10px] font-medium px-2 py-1 rounded-full ${h.tone === "warn" ? "bg-[color:color-mix(in_oklab,var(--warning)_22%,white)] text-[color:color-mix(in_oklab,var(--warning)_60%,black)]" : "bg-mint text-sage"}`}>{h.tag}</span>
            </div>
          ))}
        </div>
        <Link to="/simulator" className="mt-5 w-full neu-btn rounded-xl py-2 text-xs font-medium text-sage block text-center">View Full Forecast</Link>
      </div>

      {/* What-If Simulator */}
      <div className="soft-card p-5">
        <h3 className="font-display text-lg font-semibold flex items-center gap-2">What-If Simulator <Info className="w-3.5 h-3.5 text-muted-foreground" /></h3>
        <p className="text-[11px] text-muted-foreground mt-1">See how small changes can improve your future health.</p>
        <div className="text-[11px] text-muted-foreground mt-3">I want to improve <button className="ml-2 neu-btn px-2 py-1 rounded-lg inline-flex items-center gap-1 text-foreground">Heart Health <ChevronDown className="w-3 h-3" /></button></div>

        <div className="mt-3 space-y-3">
          <SliderRow label="Walk 30 min daily" value={walk} setValue={setWalk} max={60} delta={`+${Math.round(walk * 0.7)}%`} />
          <SliderRow label="Sleep +1 hour" value={sleep} setValue={setSleep} max={3} delta={`+${sleep * 18}%`} />
          <SliderRow label="Reduce stress 20%" value={stress} setValue={setStress} max={50} delta={`+${Math.round(stress * 0.75)}%`} />
        </div>
        <div className="mt-4">
          <div className="text-[11px] text-muted-foreground">Predicted improvement in 6 months</div>
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-display font-semibold text-sage">+{improvement}%</div>
            <ArrowUpRight className="w-4 h-4 text-sage" />
          </div>
          <div className="-mx-2 mt-1">
            <ResponsiveContainer width="100%" height={36}>
              <LineChart data={forecastData}>
                <Line dataKey="v" stroke="oklch(0.62 0.12 160)" strokeWidth={2} dot={false} type="monotone" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Today's Insights */}
      <div className="soft-card p-5">
        <h3 className="font-display text-lg font-semibold flex items-center gap-2">Today's Insights <Sparkles className="w-3.5 h-3.5 text-sage" /></h3>
        <div className="mt-4 space-y-3">
          {insights.map((it, i) => {
            const Icon = it.icon;
            return (
              <div key={i} className="flex gap-3 items-start">
                <div className={`w-9 h-9 rounded-xl grid place-items-center shrink-0 ${it.tone === "warn" ? "bg-[color:color-mix(in_oklab,var(--coral)_15%,white)] text-[color:var(--coral)]" : "bg-mint text-sage"}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className="text-xs text-foreground/80 leading-relaxed pt-1.5">{it.text}</p>
              </div>
            );
          })}
        </div>
        <Link to="/insights" className="mt-4 w-full neu-btn rounded-xl py-2 text-xs font-medium text-sage block text-center">View All Insights</Link>
      </div>

      {/* Data Reliability */}
      <div className="soft-card p-5">
        <h3 className="font-display text-lg font-semibold flex items-center gap-2">Data Reliability <Info className="w-3.5 h-3.5 text-muted-foreground" /></h3>
        <div className="mt-4 space-y-3.5">
          {trust.map((t) => {
            const Icon = t.icon;
            return (
              <div key={t.label} className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-mint/70 grid place-items-center text-sage"><Icon className="w-4 h-4" /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs font-medium truncate">{t.label}</div>
                    <div className="text-[10px] text-muted-foreground">{t.note}</div>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-mint/60 overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{ width: `${t.val}%`, background: t.tone === "warn" ? "var(--warning)" : "var(--sage)" }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <Link to="/trust" className="mt-4 w-full neu-btn rounded-xl py-2 text-xs font-medium text-sage block text-center">View Trust Details</Link>
      </div>
    </section>
  );
}

function SliderRow({ label, value, setValue, max, delta }: { label: string; value: number; setValue: (n: number) => void; max: number; delta: string }) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-foreground/80">{label}</span>
        <span className="text-sage font-semibold">{delta}</span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
        className="w-full mt-1 accent-[color:var(--sage)]"
      />
    </div>
  );
}
