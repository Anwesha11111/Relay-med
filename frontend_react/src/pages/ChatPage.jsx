import AppShell from '../components/AppShell';
import ChatWidget from '../components/ChatWidget';
import { mockUser } from '../mockData';
import { Bot, Zap } from 'lucide-react';

export default function ChatPage() {
  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', height:'calc(100vh - 80px)', gap:0 }}>
        {/* Header */}
        <div style={{ marginBottom:20 }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:6 }}>
            <div style={{ width:40, height:40, borderRadius:12,
              background:'linear-gradient(135deg,#00D4FF,#7C3AED)',
              display:'flex', alignItems:'center', justifyContent:'center',
              boxShadow:'0 0 16px rgba(0,212,255,0.3)' }}>
              <Bot size={20} color="white"/>
            </div>
            <div>
              <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:22, fontWeight:800,
                color:'#F9FAFB', margin:0 }}>RelayMed AI Assistant</h1>
              <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:2 }}>
                <div style={{ width:7, height:7, borderRadius:'50%', background:'#10B981',
                  boxShadow:'0 0 6px #10B981', animation:'pulse 2s infinite' }} />
                <span style={{ fontSize:12, color:'#10B981', fontFamily:'DM Sans,sans-serif' }}>
                  Online · Using {mockUser.abhaId ? 'your health context' : 'general knowledge'}
                </span>
              </div>
            </div>
          </div>
          <p style={{ fontSize:13, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
            Ask about your health signals, scores, trends, and what actions might help. 
            <span style={{ color:'#F59E0B' }}> Not a substitute for medical advice.</span>
          </p>
        </div>

        {/* Chat widget in a card */}
        <div className="glass-card" style={{ flex:1, display:'flex', flexDirection:'column',
          overflow:'hidden', minHeight:0 }}>
          <ChatWidget />
        </div>

        <style>{`
          @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }
        `}</style>
      </div>
    </AppShell>
  );
}
