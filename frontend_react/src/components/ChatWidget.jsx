import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader } from 'lucide-react';

const MOCK_REPLIES = [
  "Based on your recent health data, I see a consistent sleep signal that's worth paying attention to. Your resting heart rate has also been slightly elevated — these two patterns often correlate. I'd suggest discussing this with your healthcare provider at your next visit.",
  "Great question! Your cardiometabolic score is currently in the 'worth monitoring' range. The good news is your respiratory and renal signals look healthy. The top action item for you this week is improving sleep consistency — even 30 extra minutes per night compounds significantly.",
  "Looking at your trajectory, if you maintain your current medication adherence streak and improve sleep to 7+ hours, your score could improve by 8–12 points over the next 3 months. These are signals, not diagnoses — always consult your doctor for personalized guidance.",
  "Your family health data shows shared risk patterns between you and your father, particularly in cardiometabolic signals. This may have genetic and lifestyle components. Sharing this context with your family doctor could be valuable.",
  "I'm RelayMed AI, not a substitute for professional medical care. I can help you understand your health signals and trends. For anything that feels urgent — chest pain, difficulty breathing, or severe symptoms — please contact emergency services or your doctor immediately.",
];

let mockIdx = 0;

async function* streamMockReply(msg) {
  // Pick a contextual reply
  let reply = MOCK_REPLIES[mockIdx % MOCK_REPLIES.length];
  mockIdx++;
  if (msg.toLowerCase().includes('sleep')) reply = MOCK_REPLIES[0];
  else if (msg.toLowerCase().includes('score') || msg.toLowerCase().includes('improve')) reply = MOCK_REPLIES[2];
  else if (msg.toLowerCase().includes('family') || msg.toLowerCase().includes('dad')) reply = MOCK_REPLIES[3];
  else if (msg.toLowerCase().includes('emergency') || msg.toLowerCase().includes('urgent')) reply = MOCK_REPLIES[4];
  
  const words = reply.split(' ');
  for (const word of words) {
    yield word + ' ';
    await new Promise(r => setTimeout(r, 40));
  }
}

async function sendToBackend(sessionId, msg) {
  try {
    const resp = await fetch('/api/v1/conversation/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: msg, stream: false }),
    });
    if (resp.ok) {
      const data = await resp.json();
      return data.response || null;
    }
  } catch { /* backend offline */ }
  return null;
}

export default function ChatWidget() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm RelayMed AI, your health intelligence companion. I can help you understand your health signals, trends, and what they might mean. What would you like to know?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}`);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');

    setMessages(m => [...m, { id: Date.now(), role: 'user', content: userMsg }]);
    setLoading(true);

    // Try backend first, fall back to mock streaming
    const backendReply = await sendToBackend(sessionId, userMsg);

    if (backendReply) {
      setMessages(m => [...m, { id: Date.now() + 1, role: 'assistant', content: backendReply }]);
      setLoading(false);
    } else {
      // Stream mock reply
      const assistantId = Date.now() + 1;
      setMessages(m => [...m, { id: assistantId, role: 'assistant', content: '' }]);
      setLoading(false);

      let accumulated = '';
      for await (const chunk of streamMockReply(userMsg)) {
        accumulated += chunk;
        setMessages(m => m.map(msg =>
          msg.id === assistantId ? { ...msg, content: accumulated } : msg
        ));
      }
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const suggestions = [
    'What does my sleep score mean?',
    'How can I improve my health score?',
    'Tell me about my heart signals',
    'Family health risks?',
  ];

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', gap:0 }}>
      {/* Messages */}
      <div style={{ flex:1, overflowY:'auto', padding:'16px', display:'flex', flexDirection:'column', gap:14 }}>
        {messages.map(msg => (
          <div key={msg.id} style={{
            display:'flex', gap:10,
            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
            alignItems:'flex-start',
          }}>
            <div style={{
              width:32, height:32, borderRadius:'50%', flexShrink:0,
              background: msg.role === 'assistant'
                ? 'linear-gradient(135deg,#00D4FF,#7C3AED)'
                : 'rgba(255,255,255,0.1)',
              display:'flex', alignItems:'center', justifyContent:'center',
              boxShadow: msg.role==='assistant' ? '0 0 12px rgba(0,212,255,0.3)' : 'none',
            }}>
              {msg.role === 'assistant' ? <Bot size={16} color="white"/> : <User size={16} color="#9CA3AF"/>}
            </div>
            <div style={{
              maxWidth:'75%',
              background: msg.role === 'assistant'
                ? 'rgba(255,255,255,0.04)' : 'rgba(0,212,255,0.1)',
              border: msg.role === 'assistant'
                ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,212,255,0.2)',
              borderRadius: msg.role === 'assistant' ? '4px 14px 14px 14px' : '14px 4px 14px 14px',
              padding:'12px 16px',
              fontSize:14, lineHeight:1.65,
              color: msg.role === 'assistant' ? '#D1D5DB' : '#E0F7FF',
              fontFamily:'DM Sans,sans-serif',
            }}>
              {msg.content || (
                <span style={{ display:'flex', gap:4, alignItems:'center', color:'#6B7280' }}>
                  <Loader size={14} style={{ animation:'spin 1s linear infinite' }} /> thinking…
                </span>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display:'flex', gap:10, alignItems:'flex-start' }}>
            <div style={{ width:32, height:32, borderRadius:'50%',
              background:'linear-gradient(135deg,#00D4FF,#7C3AED)',
              display:'flex', alignItems:'center', justifyContent:'center' }}>
              <Bot size={16} color="white"/>
            </div>
            <div style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)',
              borderRadius:'4px 14px 14px 14px', padding:'14px 18px', display:'flex', gap:6 }}>
              {[0,1,2].map(i => (
                <div key={i} style={{ width:7, height:7, borderRadius:'50%', background:'#4B5563',
                  animation:`bounce 1.2s ease-in-out ${i*0.2}s infinite` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div style={{ padding:'0 16px 12px', display:'flex', flexWrap:'wrap', gap:8 }}>
          {suggestions.map(s => (
            <button key={s} onClick={() => { setInput(s); }}
              style={{ background:'rgba(0,212,255,0.06)', border:'1px solid rgba(0,212,255,0.2)',
                color:'#7DD3FC', borderRadius:20, padding:'6px 14px', fontSize:12,
                cursor:'pointer', fontFamily:'DM Sans,sans-serif', transition:'all 0.2s' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <div style={{ padding:'6px 16px', fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif',
        borderTop:'1px solid rgba(255,255,255,0.04)', textAlign:'center' }}>
        ⚠️ RelayMed AI is not a substitute for professional medical advice
      </div>

      {/* Input */}
      <div style={{ padding:'12px 16px', borderTop:'1px solid #1F2937',
        display:'flex', gap:10, alignItems:'flex-end' }}>
        <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
          placeholder="Ask about your health signals, trends, or scores…"
          rows={1}
          style={{ flex:1, background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.1)',
            borderRadius:12, padding:'12px 16px', color:'#F9FAFB', fontFamily:'DM Sans,sans-serif',
            fontSize:14, resize:'none', outline:'none', transition:'border-color 0.2s',
            lineHeight:1.5 }}
          onFocus={e => e.target.style.borderColor = 'rgba(0,212,255,0.4)'}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
        />
        <button onClick={handleSend} disabled={!input.trim() || loading}
          style={{ background: input.trim() && !loading
            ? 'linear-gradient(135deg,#00D4FF,#7C3AED)' : 'rgba(255,255,255,0.06)',
            border:'none', borderRadius:12, padding:'12px 16px', cursor: input.trim() ? 'pointer' : 'default',
            color:'white', transition:'all 0.2s', display:'flex', alignItems:'center', justifyContent:'center',
            boxShadow: input.trim() ? '0 4px 16px rgba(0,212,255,0.25)' : 'none' }}>
          <Send size={18} />
        </button>
      </div>

      <style>{`
        @keyframes bounce {
          0%,100% { transform:translateY(0); opacity:0.4; }
          50% { transform:translateY(-4px); opacity:1; }
        }
        @keyframes spin { 100% { transform:rotate(360deg); } }
      `}</style>
    </div>
  );
}
