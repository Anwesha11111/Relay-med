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
  const [dietaryPref, setDietaryPref] = useState<string>("Veg"); // Default to Veg
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages]);
  useEffect(() => { const t = setInterval(() => setPersonalized(isDataSharingOn()), 2000); return () => clearInterval(t); }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return;
    
    const userMsg = text.trim();
    setMessages(p => [...p, { role: "user", content: userMsg }]);
    setInput(""); 
    setLoading(true);
    
    const hCtx = buildHealthContext();
    const enriched = hCtx ? userMsg + hCtx : userMsg;

    try {
      const response = await fetch(`${API_BASE}/api/v1/conversation/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          session_id: sessionId, 
          message: enriched, 
          include_health_context: true, 
          stream: true,
          dietary_preference: dietaryPref 
        }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantResponse = "";
      
      // Initialize assistant message
      setMessages(p => [...p, { role: "assistant", content: "", hasDisclaimer: false }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr === "[DONE]") continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.session_id && !sessionId) {
                setSessionId(data.session_id);
              }
              
              if (data.chunk) {
                assistantResponse += data.chunk;
                setMessages(p => {
                  const newMsgs = [...p];
                  const last = newMsgs[newMsgs.length - 1];
                  if (last && last.role === "assistant") {
                    last.content = assistantResponse;
                    last.hasDisclaimer = assistantResponse.includes("consult your doctor");
                  }
                  return newMsgs;
                });
              }
            } catch (e) {
              console.error("Error parsing stream chunk:", e, dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(p => [...p, { 
        role: "assistant", 
        content: "I'm having trouble connecting to my health intelligence core. Please check if the backend is running.\n\n*Technical Detail: " + (error instanceof Error ? error.message : "Unknown error") + "*",
        hasDisclaimer: false
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, sessionId, buildHealthContext]);

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } };

  const renderInline = (text: string, key: string) => {
    const parts: React.ReactNode[] = [];
    const re = /(\*\*[^*]+\*\*|\*[^*]+\*|--)/g;
    let last = 0, m, idx = 0;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push(<span key={`${key}-${idx++}`}>{text.slice(last, m.index)}</span>);
      const s = m[0];
      if (s.startsWith("**") && s.endsWith("**")) parts.push(<strong key={`${key}-${idx++}`} className="text-ocean dark:text-cyan-400">{s.slice(2, -2)}</strong>);
      else if (s.startsWith("*") && s.endsWith("*")) parts.push(<em key={`${key}-${idx++}`} className="text-muted-foreground italic">{s.slice(1, -1)}</em>);
      else if (s === "--") parts.push(<span key={`${key}-${idx++}`}> — </span>);
      last = m.index + s.length;
    }
    if (last < text.length) parts.push(<span key={`${key}-${idx}`}>{text.slice(last)}</span>);
    return parts.length > 0 ? parts : [<span key={key}>{text}</span>];
  };

  const renderContent = (text: string) => text.split("\n").map((line, i) => {
    const k = `l${i}`;
    if (line.startsWith("---")) return <hr key={k} className="my-3 border-t border-gray-200 dark:border-gray-800" />;
    if (line === "") return <div key={k} className="h-2" />;
    if (/^\d+\.\s/.test(line)) return <span key={k} className="block ml-3 text-sm mb-1">{renderInline(line, k)}</span>;
    if (line.startsWith("- ")) return <span key={k} className="block ml-3 text-sm mb-1">{renderInline(line, k)}</span>;
    return <span key={k} className="block text-sm leading-relaxed mb-1">{renderInline(line, k)}</span>;
  });

  return (
    <aside className="glass-card p-6 sticky top-6 fade-in flex flex-col border-white/20 shadow-2xl backdrop-blur-xl" style={{ maxHeight: "calc(100vh - 3rem)", background: "rgba(255, 255, 255, 0.7)" }}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="relative w-12 h-12 rounded-2xl gradient-ocean grid place-items-center text-white shadow-lg animate-pulse-ring">
            <Bot className="w-6 h-6" />
            <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white shadow-sm" />
          </div>
          <div>
            <div className="font-display text-lg font-bold tracking-tight text-ocean leading-tight">Relay Guide</div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest flex items-center gap-1.5 mt-0.5">
              Smart Health Intelligence
            </div>
          </div>
        </div>
        <button className="p-2 hover:bg-black/5 rounded-xl transition-colors"><MoreVertical className="w-5 h-5 text-muted-foreground" /></button>
      </div>

      <div className="mt-4 flex items-center gap-3 bg-amber-50/80 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/50 rounded-2xl px-4 py-3 shadow-sm backdrop-blur-sm">
        <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0" />
        <span className="text-[11px] text-amber-800 dark:text-amber-200 leading-snug font-medium">
          Smart guidance mode. Always consult your healthcare provider for clinical decisions.
        </span>
      </div>

      <div className={`mt-3 flex items-center gap-2.5 rounded-2xl px-4 py-2 text-[11px] font-medium transition-all duration-500 ${personalized ? "bg-emerald-50/80 border border-emerald-100 text-emerald-700 shadow-sm" : "bg-rose-50/80 border border-rose-100 text-rose-600"}`}>
        {personalized ? <><UserCheck className="w-4 h-4 shrink-0 animate-bounce-subtle" /> Intelligence Core: Active & Personalized</> : <><UserX className="w-4 h-4 shrink-0" /> intelligence Core: Generic (Sharing Disabled)</>}
      </div>

      {/* Dietary preferences removed as per user request */}

      <div ref={scrollRef} className="mt-5 space-y-4 overflow-y-auto pr-2 flex-1 scrollbar-hide" style={{ minHeight: "240px" }}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`rounded-3xl px-4 py-3 text-sm max-w-[92%] shadow-sm ${msg.role === "user" ? "rounded-tr-lg bg-gradient-to-br from-ocean to-blue-600 text-white" : "rounded-tl-lg bg-white/80 border border-white/40 backdrop-blur-sm text-slate-700 leading-relaxed"}`}>
              {renderContent(msg.content)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-3xl rounded-tl-lg bg-white/60 border border-white/40 px-4 py-3 flex items-center gap-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-ocean rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-ocean rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-ocean rounded-full animate-bounce" />
              </div>
              <span className="text-slate-500 text-xs font-medium italic">Relay Guide is analyzing...</span>
            </div>
          </div>
        )}
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
