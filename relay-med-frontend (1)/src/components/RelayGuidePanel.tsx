import { Bot, Send, MoreVertical, Loader2, ShieldAlert, UserCheck, UserX } from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const suggestions = [
  "What factors are increasing my cardiovascular risk?",
  "How do I treat a burn at home?",
  "What medicine can help with headaches?",
  "Find doctors and pharmacies near me",
  "What should I apply on bruises?",
  "How will my health change in 6 months?",
];

interface ChatMessage { role: "user" | "assistant"; content: string; hasDisclaimer?: boolean; }

function getUserHealthData(): Record<string, string> | null {
  try { const r = localStorage.getItem("relaymed_health_data"); if (r) return JSON.parse(r); } catch {} return null;
}
function isDataSharingOn(): boolean {
  try { const v = localStorage.getItem("relaymed_data_sharing"); if (v !== null) return JSON.parse(v); } catch {} return true;
}
function buildHealthContext(): string {
  if (!isDataSharingOn()) return "";
  const d = getUserHealthData();
  if (!d || Object.keys(d).length === 0) return "";
  const p: string[] = [];
  if (d.blood_glucose) p.push(`Blood Glucose: ${d.blood_glucose} mg/dL`);
  if (d.systolic && d.diastolic) p.push(`BP: ${d.systolic}/${d.diastolic} mmHg`);
  if (d.spo2) p.push(`SpO2: ${d.spo2}%`);
  if (d.heart_rate) p.push(`HR: ${d.heart_rate} bpm`);
  if (d.temperature) p.push(`Temp: ${d.temperature}°F`);
  if (d.weight) p.push(`Weight: ${d.weight} kg`);
  if (d.fitbit_steps) p.push(`Steps: ${d.fitbit_steps}`);
  if (d.fitbit_sleep) p.push(`Sleep: ${d.fitbit_sleep} hrs`);
  if (d.conditions) p.push(`Conditions: ${d.conditions}`);
  if (d.medications) p.push(`Medications: ${d.medications}`);
  return p.length ? "\n\n[My Health Data: " + p.join(" | ") + "]" : "";
}

const WELCOME: ChatMessage = {
  role: "assistant",
  content: "Hello! I'm Relay Guide, your AI health companion. I can help you understand your health data, suggest lifestyle changes, answer general medical questions, and even discuss medicines — though I'll always remind you to check with your doctor first.\n\nHow can I support your health today?",
};

export function RelayGuidePanel() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [personalized, setPersonalized] = useState(isDataSharingOn());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);
  useEffect(() => { const t = setInterval(() => setPersonalized(isDataSharingOn()), 2000); return () => clearInterval(t); }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages(p => [...p, { role: "user", content: text.trim() }]);
    setInput(""); setLoading(true);
    const hCtx = buildHealthContext();
    const enriched = hCtx ? text.trim() + hCtx : text.trim();
    try {
      const res = await fetch(`${API_BASE}/api/v1/conversation/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: enriched, include_health_context: true, stream: false }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      let resp = data.response || "I'm having trouble right now. Please try again.";
      if (hCtx && !resp.includes("Based on your health data")) resp = "*(Personalized based on your health data)*\n\n" + resp;
      setMessages(p => [...p, { role: "assistant", content: resp, hasDisclaimer: resp.includes("consult your doctor") }]);
    } catch {
      setMessages(p => [...p, { role: "assistant", content: "I'm currently in demo mode (backend connecting...). In production, I analyze your health data and provide personalized insights, including medicine suggestions with appropriate disclaimers.\n\nThis is AI-generated guidance. AI can make mistakes. Please consult a qualified healthcare provider before making any medical decisions." }]);
    } finally { setLoading(false); }
  }, [loading, sessionId]);

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } };

  const renderInline = (text: string, key: string) => {
    const parts: React.ReactNode[] = [];
    const re = /(\*\*[^*]+\*\*|\*[^*]+\*|--)/g;
    let last = 0, m, idx = 0;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push(<span key={`${key}-${idx++}`}>{text.slice(last, m.index)}</span>);
      const s = m[0];
      if (s.startsWith("**") && s.endsWith("**")) parts.push(<strong key={`${key}-${idx++}`}>{s.slice(2, -2)}</strong>);
      else if (s.startsWith("*") && s.endsWith("*")) parts.push(<em key={`${key}-${idx++}`} className="text-muted-foreground">{s.slice(1, -1)}</em>);
      else if (s === "--") parts.push(<span key={`${key}-${idx++}`}> — </span>);
      last = m.index + s.length;
    }
    if (last < text.length) parts.push(<span key={`${key}-${idx}`}>{text.slice(last)}</span>);
    return parts.length > 0 ? parts : [<span key={key}>{text}</span>];
  };

  const renderContent = (text: string) => text.split("\n").map((line, i) => {
    const k = `l${i}`;
    if (line.startsWith("---")) return <hr key={k} className="my-2 border-t border-gray-200" />;
    if (line === "") return <br key={k} />;
    if (/^\d+\.\s/.test(line)) return <span key={k} className="block ml-3 text-sm">{renderInline(line, k)}</span>;
    if (line.startsWith("- ")) return <span key={k} className="block ml-3 text-sm">{renderInline(line, k)}</span>;
    return <span key={k} className="block text-sm">{renderInline(line, k)}</span>;
  });

  return (
    <aside className="soft-card p-5 sticky top-6 fade-in flex flex-col" style={{ maxHeight: "calc(100vh - 3rem)" }}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="relative w-11 h-11 rounded-2xl gradient-sage grid place-items-center text-white animate-pulse-ring"><Bot className="w-5 h-5" /></div>
          <div>
            <div className="font-display text-base font-semibold leading-tight">Relay Guide</div>
            <div className="text-[11px] text-muted-foreground">AI Health Companion</div>
            <div className="text-[10px] text-sage flex items-center gap-1 mt-0.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" /> Online</div>
          </div>
        </div>
        <MoreVertical className="w-4 h-4 text-muted-foreground" />
      </div>

      <div className="mt-3 flex items-center gap-2 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl px-3 py-2">
        <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
        <span className="text-[10px] text-amber-700 dark:text-amber-300 leading-tight">AI can suggest medicines but may make mistakes. Always consult your doctor before taking any medication.</span>
      </div>

      <div className={`mt-2 flex items-center gap-2 rounded-xl px-3 py-1.5 text-[10px] ${personalized ? "bg-emerald-50 border border-emerald-200 text-emerald-700" : "bg-red-50 border border-red-200 text-red-600"}`}>
        {personalized ? <><UserCheck className="w-3.5 h-3.5 shrink-0" /> Personalized — using your health data for tailored responses</> : <><UserX className="w-3.5 h-3.5 shrink-0" /> Generic mode — enable data sharing in Settings for personalized responses</>}
      </div>

      <div ref={scrollRef} className="mt-4 space-y-3 overflow-y-auto pr-1 flex-1" style={{ minHeight: "200px" }}>
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "rounded-2xl rounded-tr-md ml-auto px-3.5 py-2.5 text-sm max-w-[90%]" : "rounded-2xl rounded-tl-md px-3.5 py-2.5 text-sm leading-relaxed bg-mint/40"} style={msg.role === "user" ? { background: "color-mix(in oklab, var(--ocean) 14%, white)" } : undefined}>
            {renderContent(msg.content)}
          </div>
        ))}
        {loading && <div className="rounded-2xl rounded-tl-md bg-mint/40 px-3.5 py-2.5 text-sm flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin text-sage" /><span className="text-muted-foreground text-xs">Relay Guide is thinking...</span></div>}
      </div>

      <div className="space-y-1.5 pt-2 border-t mt-2">
        <div className="text-[10px] text-muted-foreground uppercase tracking-wider px-1">Suggested</div>
        {suggestions.slice(0, 4).map((s) => (
          <button key={s} onClick={() => sendMessage(s)} disabled={loading} className="w-full text-left text-xs px-3 py-2 rounded-xl bg-white hover:bg-mint/60 border transition-colors disabled:opacity-50">{s}</button>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2 bg-white rounded-2xl border px-3 py-2 shadow-sm">
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Ask me anything..." disabled={loading} className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground disabled:opacity-50" />
        <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} className="w-8 h-8 rounded-xl gradient-sage grid place-items-center text-white hover:scale-105 transition-transform disabled:opacity-50">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
