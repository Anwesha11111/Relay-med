import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { Settings as SettingsIcon, ShieldCheck, Database, Eye, EyeOff, User, Bell, Brain, Lock, LogOut, Info, Monitor, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export const Route = createFileRoute("/settings")({ component: Page });

function Toggle({ label, desc, defaultOn = false, onChange, storageKey }: { label: string; desc: string; defaultOn?: boolean; onChange?: (val: boolean) => void; storageKey?: string }) {
  const [on, setOn] = useState(() => {
    if (storageKey) { try { const v = localStorage.getItem(storageKey); if (v !== null) return JSON.parse(v); } catch {} }
    return defaultOn;
  });
  return (
    <div className="flex items-center justify-between rounded-2xl border bg-white p-4">
      <div className="flex-1 mr-4">
        <div className="font-medium text-sm">{label}</div>
        <div className="text-xs text-muted-foreground leading-relaxed">{desc}</div>
      </div>
      <button
        onClick={() => { const next = !on; setOn(next); onChange?.(next); if (storageKey) localStorage.setItem(storageKey, JSON.stringify(next)); }}
        className={`w-11 h-6 rounded-full p-0.5 transition-colors shrink-0 ${on ? "bg-sage" : "bg-mint"}`}
        style={{ background: on ? "var(--sage)" : "var(--mint)" }}
      >
        <span className={`block w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${on ? "translate-x-5" : ""}`} />
      </button>
    </div>
  );
}

function SectionHeader({ icon: Icon, title, subtitle }: { icon: React.ElementType; title: string; subtitle: string }) {
  return (
    <div className="flex items-center gap-3 mb-3 mt-6 first:mt-0">
      <div className="w-9 h-9 rounded-xl bg-mint grid place-items-center text-sage shrink-0">
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <div className="font-display font-semibold text-sm">{title}</div>
        <div className="text-[11px] text-muted-foreground">{subtitle}</div>
      </div>
    </div>
  );
}

function Page() {
  const { user, logout } = useAuth();
  const [dataSharing, setDataSharing] = useState(true);
  const [showSyncModal, setShowSyncModal] = useState(false);

  const displayName = user?.name || "User";
  const initial = displayName.charAt(0).toUpperCase();
  const provider = user?.provider || "email";
  const providerLabel = provider === "google" ? "Google" : provider === "twitter" ? "Twitter" : "Email";

  return (
    <PageShell title="Settings" subtitle="Personalize your Relay-med experience, privacy, and data preferences." icon={SettingsIcon}>
      <div className="max-w-3xl space-y-2">

        {/* ── Account ─────────────────────────────────── */}
        <SectionHeader icon={User} title="Account" subtitle="Manage your profile and login" />
        <div className="rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full gradient-sage grid place-items-center text-white font-bold text-lg">{initial}</div>
            <div className="flex-1">
              <div className="font-semibold">{displayName}</div>
              <div className="text-xs text-muted-foreground">{user?.email || "user@relaymed.com"}</div>
              <div className="text-[10px] text-sage mt-0.5">Connected via {providerLabel}</div>
            </div>
            <button
              onClick={logout}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 border rounded-lg px-3 py-1.5"
            >
              <LogOut className="w-3 h-3" /> Sign Out
            </button>
          </div>
        </div>

        {/* ── Sync Devices ─────────────────────────────── */}
        <SectionHeader icon={Monitor} title="Sync Devices" subtitle="Manage connected devices" />
        <div className="rounded-2xl border bg-white p-4">
          <div className="space-y-3">
            {[
              { name: "This Device", type: "Desktop — Chrome", synced: true, last: "Now" },
              { name: `${displayName}'s Phone`, type: "Mobile — Relay-med App", synced: true, last: "2h ago" },
              { name: "Tablet", type: "iPad — Safari", synced: false, last: "Never" },
            ].map((d) => (
              <div key={d.name} className="flex items-center justify-between py-1">
                <div className="flex items-center gap-3">
                  <Monitor className="w-4 h-4 text-sage" />
                  <div>
                    <div className="text-sm font-medium">{d.name}</div>
                    <div className="text-[10px] text-muted-foreground">{d.type} — Last sync: {d.last}</div>
                  </div>
                </div>
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${d.synced ? "bg-mint text-sage" : "bg-gray-100 text-gray-500"}`}>
                  {d.synced ? "Synced" : "Not synced"}
                </span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground mt-3 leading-relaxed">
            Same account = same data. Sign in on another device with your {providerLabel} account to access your health data there.
          </p>
        </div>

        {/* ── Notifications ──────────────────────────── */}
        <SectionHeader icon={Bell} title="Notifications" subtitle="Control how you receive updates" />
        <div className="space-y-2">
          <Toggle label="Daily wellness summaries" desc="Receive a calm morning briefing with your health overview." defaultOn />
          <Toggle label="Anomaly alerts" desc="Get notified only about meaningful or concerning changes in your vitals." defaultOn />
          <Toggle label="Weekly progress reports" desc="Summary of your health trends and improvements every Sunday." defaultOn />
          <Toggle label="Medicine interaction warnings" desc="Alert when potential drug interactions are detected." defaultOn />
        </div>

        {/* ── Privacy & Data Sharing ─────────────────── */}
        <SectionHeader icon={ShieldCheck} title="Privacy & Data Sharing" subtitle="Control what data the AI can access" />

        <div className="rounded-2xl border bg-amber-50 dark:bg-amber-950/30 border-amber-200 p-4 mb-2">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 dark:text-amber-200 leading-relaxed">
              <strong>How data sharing affects your experience:</strong> AI personalized results may vary based on
              how much data you share. More data enables more accurate health insights, trend detection, and
              personalized recommendations. You can change these settings at any time — your data is always kept
              safe but the AI simply won't use it when sharing is disabled.
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Toggle
            label="Allow AI to use my health data"
            desc="Master switch — when off, AI will not access any of your previously shared data for personalization. Your data is kept but not used."
            defaultOn={dataSharing}
            onChange={setDataSharing}
            storageKey="relaymed_data_sharing"
          />

          {!dataSharing && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-xs text-red-700 ml-4">
              AI personalization is currently <strong>disabled</strong>. You will receive generic health guidance instead of personalized insights.
              Your existing data is safely stored and can be re-enabled at any time by toggling this switch back on.
            </div>
          )}

          <Toggle label="Share vital signs (HR, BP, SpO2)" desc="Allow AI to analyze your heart rate, blood pressure, and oxygen levels." defaultOn />
          <Toggle label="Share activity data (Steps, Sleep)" desc="Allow AI to factor in your physical activity and sleep patterns." defaultOn />
          <Toggle label="Share medical history" desc="Include conditions, allergies, and past diagnoses in AI analysis." />
          <Toggle label="Share medical certificates & documents" desc="Allow uploaded medical documents to be referenced by the AI." />
          <Toggle label="Share with clinician" desc="Allow your verified clinician to view your reports and AI insights." />
        </div>

        {/* ── Data Permissions ────────────────────────── */}
        <SectionHeader icon={Database} title="Data Permissions Log" subtitle="See what you've shared and when" />
        <div className="rounded-2xl border bg-white p-4 space-y-3">
          {[
            { type: "Vital Signs", status: "Shared", date: "Active since Jan 2026", shared: true },
            { type: "Activity Data", status: "Shared", date: "Active since Feb 2026", shared: true },
            { type: "Medical History", status: "Not shared", date: "Never shared", shared: false },
            { type: "Medical Certificates", status: "Not shared", date: "Never shared", shared: false },
            { type: "Clinician Access", status: "Not shared", date: "Never shared", shared: false },
          ].map((item) => (
            <div key={item.type} className="flex items-center justify-between py-1">
              <div className="flex items-center gap-3">
                {item.shared
                  ? <Eye className="w-4 h-4 text-sage" />
                  : <EyeOff className="w-4 h-4 text-muted-foreground" />
                }
                <div>
                  <div className="text-sm font-medium">{item.type}</div>
                  <div className="text-[10px] text-muted-foreground">{item.date}</div>
                </div>
              </div>
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                item.shared ? "bg-mint text-sage" : "bg-gray-100 text-gray-500"
              }`}>
                {item.status}
              </span>
            </div>
          ))}
        </div>

        {/* ── AI Preferences ─────────────────────────── */}
        <SectionHeader icon={Brain} title="AI Preferences" subtitle="Customize AI behavior" />
        <div className="space-y-2">
          <Toggle label="Personalized medicine suggestions" desc="Allow AI to suggest specific medicines (always with consult-a-doctor warning)." defaultOn />
          <Toggle label="Proactive health alerts" desc="AI will proactively flag concerning trends without you asking." defaultOn />
          <Toggle label="Include drug interaction checks" desc="AI will cross-reference suggested medicines with your known medications." defaultOn />
          <Toggle label="Federated learning opt-in" desc="Help improve the AI model — your data never leaves your device." />
        </div>

        {/* ── Security ────────────────────────────────── */}
        <SectionHeader icon={Lock} title="Security" subtitle="Protect your account" />
        <div className="rounded-2xl border bg-white p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Encryption</div>
              <div className="text-[10px] text-muted-foreground">All data encrypted with AES-256</div>
            </div>
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-mint text-sage">Active</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Two-Factor Authentication</div>
              <div className="text-[10px] text-muted-foreground">Add extra security to your account</div>
            </div>
            <button className="text-xs text-sage hover:underline">Enable</button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Login Sessions</div>
              <div className="text-[10px] text-muted-foreground">Signed in via {providerLabel} — {new Date().toLocaleDateString()}</div>
            </div>
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-mint text-sage">Active</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Data Export</div>
              <div className="text-[10px] text-muted-foreground">Download all your health data</div>
            </div>
            <button className="text-xs text-sage hover:underline">Export</button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-red-600">Delete Account</div>
              <div className="text-[10px] text-muted-foreground">Permanently remove all data</div>
            </div>
            <button className="text-xs text-red-500 hover:underline">Delete</button>
          </div>
        </div>

      </div>
    </PageShell>
  );
}
