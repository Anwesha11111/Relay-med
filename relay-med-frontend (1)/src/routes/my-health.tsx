import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { HeartPulse, Moon, Footprints, Droplet, Flame, Activity, MapPin, Phone, Pill, Stethoscope, Upload, Watch, Thermometer, Save, Check, AlertCircle } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { useState, useEffect } from "react";

export const Route = createFileRoute("/my-health")({ component: Page });

const vitals = [
  { icon: HeartPulse, label: "Resting Heart Rate", v: "62 bpm", trend: "Normal", color: "oklch(0.72 0.16 30)" },
  { icon: Moon, label: "Sleep", v: "7h 24m", trend: "Good", color: "oklch(0.66 0.11 230)" },
  { icon: Footprints, label: "Steps Today", v: "8,420", trend: "On track", color: "oklch(0.62 0.12 160)" },
  { icon: Droplet, label: "Hydration", v: "1.6 L", trend: "Below target", color: "oklch(0.66 0.11 230)" },
  { icon: Flame, label: "Calories Burned", v: "2,140", trend: "Healthy", color: "oklch(0.72 0.16 30)" },
  { icon: Activity, label: "Stress Score", v: "42", trend: "Elevated", color: "oklch(0.72 0.16 30)" },
];

interface HealthData {
  blood_glucose?: string; systolic?: string; diastolic?: string; spo2?: string;
  heart_rate?: string; temperature?: string; weight?: string;
  fitbit_steps?: string; fitbit_sleep?: string; conditions?: string; medications?: string;
  [key: string]: string | undefined;
}

function loadHealthData(): HealthData {
  try { const r = localStorage.getItem("relaymed_health_data"); if (r) return JSON.parse(r); } catch {} return {};
}
function saveHealthData(d: HealthData) { localStorage.setItem("relaymed_health_data", JSON.stringify(d)); }

function Page() {
  const [healthData, setHealthData] = useState<HealthData>(loadHealthData);
  const [saved, setSaved] = useState(false);
  const [reports, setReports] = useState<string[]>([]);

  const [dataSharing] = useState(() => { try { const v = localStorage.getItem("relaymed_data_sharing"); return v !== null ? JSON.parse(v) : true; } catch {} return true; });
  const [shareVitals] = useState(() => { try { const v = localStorage.getItem("relaymed_share_vitals"); return v !== null ? JSON.parse(v) : true; } catch {} return true; });
  const [shareActivity] = useState(() => { try { const v = localStorage.getItem("relaymed_share_activity"); return v !== null ? JSON.parse(v) : true; } catch {} return true; });
  const [shareMedicalHistory] = useState(() => { try { const v = localStorage.getItem("relaymed_share_history"); return v !== null ? JSON.parse(v) : false; } catch {} return false; });
  const [shareDocs] = useState(() => { try { const v = localStorage.getItem("relaymed_share_docs"); return v !== null ? JSON.parse(v) : false; } catch {} return false; });

  const canSaveVitals = dataSharing && shareVitals;
  const canSaveActivity = dataSharing && shareActivity;
  const canSaveHistory = dataSharing && shareMedicalHistory;
  const canSaveDocs = dataSharing && shareDocs;

  useEffect(() => {
    try { const r = localStorage.getItem("relaymed_reports"); if (r) setReports(JSON.parse(r)); } catch {}
  }, []);

  const update = (key: string, val: string) => setHealthData(prev => ({ ...prev, [key]: val }));

  const handleSave = () => {
    if (!dataSharing) {
      alert("Data Sharing is currently disabled in your settings. Please enable it to save your data.");
      return;
    }
    saveHealthData(healthData);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!canSaveDocs) {
      alert("Document sharing is disabled in your settings.");
      return;
    }
    const files = e.target.files;
    if (!files) return;
    const names = [...reports];
    for (let i = 0; i < files.length; i++) names.push(files[i].name);
    setReports(names);
    localStorage.setItem("relaymed_reports", JSON.stringify(names));
  };

  const openNearby = (type: string) => {
    window.open(`https://www.google.com/maps/search/${encodeURIComponent(type + " near me")}`, "_blank");
  };

  return (
    <PageShell title="My Health" subtitle="A complete picture of your daily vitals, device data, and wellness signals." icon={HeartPulse}>
      {/* Vitals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vitals.map((v) => {
          const Icon = v.icon;
          const data = Array.from({ length: 14 }, (_, i) => ({ v: 50 + Math.sin(i / 1.3) * 12 + i }));
          return (
            <div key={v.label} className="rounded-2xl border bg-white p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-mint/70 grid place-items-center text-sage"><Icon className="w-5 h-5" /></div>
                <div>
                  <div className="text-xs text-muted-foreground">{v.label}</div>
                  <div className="text-xl font-display font-semibold">{v.v}</div>
                </div>
              </div>
              <div className="text-[11px] mt-1 text-muted-foreground">{v.trend}</div>
              <div className="-mx-2 mt-2">
                <ResponsiveContainer width="100%" height={50}>
                  <AreaChart data={data}>
                    <defs><linearGradient id={`mh-${v.label}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={v.color} stopOpacity={0.4} /><stop offset="100%" stopColor={v.color} stopOpacity={0} /></linearGradient></defs>
                    <Area type="monotone" dataKey="v" stroke={v.color} strokeWidth={2} fill={`url(#mh-${v.label})`} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Nearby Services ── */}
      <div className="mt-8">
        <h2 className="font-display text-lg font-semibold mb-1">Nearby Services</h2>
        <p className="text-sm text-muted-foreground mb-4">Find healthcare services near your location</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={() => openNearby("doctors")} className="rounded-2xl border bg-white p-5 hover:shadow-lg hover:border-sage/40 transition-all text-left group">
            <div className="w-12 h-12 rounded-xl bg-blue-50 grid place-items-center text-blue-600 mb-3 group-hover:scale-110 transition-transform"><Stethoscope className="w-6 h-6" /></div>
            <div className="font-semibold text-sm">Find Doctors Near Me</div>
            <div className="text-xs text-muted-foreground mt-1">Opens Google Maps with nearby clinics and hospitals</div>
          </button>
          <button onClick={() => openNearby("pharmacies")} className="rounded-2xl border bg-white p-5 hover:shadow-lg hover:border-sage/40 transition-all text-left group">
            <div className="w-12 h-12 rounded-xl bg-green-50 grid place-items-center text-green-600 mb-3 group-hover:scale-110 transition-transform"><Pill className="w-6 h-6" /></div>
            <div className="font-semibold text-sm">Find Pharmacies Near Me</div>
            <div className="text-xs text-muted-foreground mt-1">Locate nearby pharmacies for prescriptions and OTC medicines</div>
          </button>
          <a href="tel:112" className="rounded-2xl border bg-red-50 border-red-200 p-5 hover:shadow-lg transition-all text-left group block">
            <div className="w-12 h-12 rounded-xl bg-red-100 grid place-items-center text-red-600 mb-3 group-hover:scale-110 transition-transform"><Phone className="w-6 h-6" /></div>
            <div className="font-semibold text-sm text-red-700">Emergency Call (112)</div>
            <div className="text-xs text-red-500 mt-1">Tap to call emergency services immediately</div>
          </a>
        </div>
      </div>

      {/* ── Medical Data Input ── */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-display text-lg font-semibold">My Medical Data</h2>
          <button onClick={handleSave} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${saved ? "bg-emerald-100 text-emerald-700" : "gradient-sage text-white hover:opacity-90"}`}>
            {saved ? <><Check className="w-4 h-4" /> Saved!</> : <><Save className="w-4 h-4" /> Save Data</>}
          </button>
        </div>
        <p className="text-sm text-muted-foreground mb-4">Enter your readings from medical devices. This data personalizes your AI health responses.</p>

        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 mb-4 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span className="text-xs text-amber-700 leading-relaxed"><strong>How this works:</strong> When you save your readings, the AI chat will reference your actual data to provide personalized health guidance. For example, if you enter high blood glucose, the AI will tailor its diabetes advice specifically to your reading.</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Glucometer */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-purple-50 grid place-items-center text-purple-600"><Droplet className="w-4 h-4" /></div>
              <div className="font-medium text-sm">Glucometer</div>
            </div>
            <label className="text-xs text-muted-foreground">Blood Glucose (mg/dL)</label>
            <input type="number" value={healthData.blood_glucose || ""} onChange={e => update("blood_glucose", e.target.value)} disabled={!canSaveVitals} placeholder="e.g. 110" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
          </div>

          {/* BP Machine */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-red-50 grid place-items-center text-red-600"><HeartPulse className="w-4 h-4" /></div>
              <div className="font-medium text-sm">BP Machine</div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><label className="text-xs text-muted-foreground">Systolic</label><input type="number" value={healthData.systolic || ""} onChange={e => update("systolic", e.target.value)} disabled={!canSaveVitals} placeholder="120" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" /></div>
              <div><label className="text-xs text-muted-foreground">Diastolic</label><input type="number" value={healthData.diastolic || ""} onChange={e => update("diastolic", e.target.value)} disabled={!canSaveVitals} placeholder="80" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" /></div>
            </div>
          </div>

          {/* Oximeter */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-blue-50 grid place-items-center text-blue-600"><Activity className="w-4 h-4" /></div>
              <div className="font-medium text-sm">Pulse Oximeter</div>
            </div>
            <label className="text-xs text-muted-foreground">SpO2 (%)</label>
            <input type="number" value={healthData.spo2 || ""} onChange={e => update("spo2", e.target.value)} disabled={!canSaveVitals} placeholder="e.g. 98" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
            <label className="text-xs text-muted-foreground mt-2 block">Heart Rate (bpm)</label>
            <input type="number" value={healthData.heart_rate || ""} onChange={e => update("heart_rate", e.target.value)} disabled={!canSaveVitals} placeholder="e.g. 72" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
          </div>

          {/* Thermometer */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-orange-50 grid place-items-center text-orange-600"><Thermometer className="w-4 h-4" /></div>
              <div className="font-medium text-sm">Thermometer</div>
            </div>
            <label className="text-xs text-muted-foreground">Temperature (°F)</label>
            <input type="number" step="0.1" value={healthData.temperature || ""} onChange={e => update("temperature", e.target.value)} disabled={!canSaveVitals} placeholder="e.g. 98.6" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
            <label className="text-xs text-muted-foreground mt-2 block">Weight (kg)</label>
            <input type="number" step="0.1" value={healthData.weight || ""} onChange={e => update("weight", e.target.value)} disabled={!canSaveVitals} placeholder="e.g. 65" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
          </div>

          {/* Fitbit / Wearable */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-teal-50 grid place-items-center text-teal-600"><Watch className="w-4 h-4" /></div>
              <div className="font-medium text-sm">Fitbit / Wearable</div>
            </div>
            <label className="text-xs text-muted-foreground">Daily Steps</label>
            <input type="number" value={healthData.fitbit_steps || ""} onChange={e => update("fitbit_steps", e.target.value)} disabled={!canSaveActivity} placeholder="e.g. 8000" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
            <label className="text-xs text-muted-foreground mt-2 block">Sleep Hours</label>
            <input type="number" step="0.1" value={healthData.fitbit_sleep || ""} onChange={e => update("fitbit_sleep", e.target.value)} disabled={!canSaveActivity} placeholder="e.g. 7.5" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
          </div>

          {/* Medical History */}
          <div className="rounded-2xl border bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 grid place-items-center text-indigo-600"><Stethoscope className="w-4 h-4" /></div>
              <div className="font-medium text-sm">Medical History</div>
            </div>
            <label className="text-xs text-muted-foreground">Known Conditions</label>
            <input type="text" value={healthData.conditions || ""} onChange={e => update("conditions", e.target.value)} disabled={!canSaveHistory} placeholder="e.g. Diabetes Type 2, Hypertension" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
            <label className="text-xs text-muted-foreground mt-2 block">Current Medications</label>
            <input type="text" value={healthData.medications || ""} onChange={e => update("medications", e.target.value)} disabled={!canSaveHistory} placeholder="e.g. Metformin 500mg, Amlodipine" className="w-full mt-1 px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50 disabled:bg-gray-50 disabled:cursor-not-allowed" />
          </div>
        </div>

        {/* Upload Medical Reports */}
        <div className="mt-4 rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-pink-50 grid place-items-center text-pink-600"><Upload className="w-4 h-4" /></div>
            <div className="font-medium text-sm">Upload Medical Reports</div>
          </div>
          <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-xl p-6 cursor-pointer hover:border-sage/40 hover:bg-mint/20 transition-colors">
            <Upload className="w-8 h-8 text-muted-foreground mb-2" />
            <span className="text-sm text-muted-foreground">Click to upload PDF, images, or documents</span>
            <span className="text-xs text-muted-foreground mt-1">Blood tests, prescriptions, X-rays, etc.</span>
            <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" onChange={handleFileUpload} className="hidden" />
          </label>
          {reports.length > 0 && (
            <div className="mt-3 space-y-1">
              <div className="text-xs text-muted-foreground font-medium">Uploaded reports:</div>
              {reports.map((r, i) => <div key={i} className="text-xs flex items-center gap-2 bg-mint/30 rounded-lg px-3 py-1.5"><Check className="w-3 h-3 text-sage" /> {r}</div>)}
            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
