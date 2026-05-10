import { useState } from 'react';
import AppShell from '../components/AppShell';
import HealthScoreWidget from '../components/HealthScoreWidget';
import RiskSignalCard from '../components/RiskSignalCard';
import AlertPanel from '../components/AlertPanel';
import { mockUser, mockHealthScore, mockRiskCards, mockAlerts, mockTimeline } from '../mockData';
import { Activity, Zap, Pill, Calendar, ChevronRight } from 'lucide-react';

const TYPE_COLORS = {
  success: '#10B981', warning: '#F59E0B', danger: '#EF4444', info: '#00D4FF',
};

function QuickStat({ icon: Icon, label, value, sub, color = '#00D4FF', dot }) {
  return (
    <div className="glass-card" style={{ padding:'18px 20px', display:'flex', gap:14, alignItems:'center' }}>
      <div style={{ width:44, height:44, borderRadius:12,
        background:`${color}18`, border:`1px solid ${color}30`,
        display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
        <Icon size={20} style={{ color }} />
      </div>
      <div style={{ flex:1, minWidth:0 }}>
        <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif',
          margin:'0 0 2px', textTransform:'uppercase', letterSpacing:'0.08em' }}>{label}</p>
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          {dot && <div style={{ width:7, height:7, borderRadius:'50%',
            background:color, boxShadow:`0 0 6px ${color}`, flexShrink:0 }} />}
          <p style={{ fontFamily:'Syne,sans-serif', fontSize:15, fontWeight:700,
            color:'#F9FAFB', margin:0, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
            {value}
          </p>
        </div>
        {sub && <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:'2px 0 0' }}>{sub}</p>}
      </div>
    </div>
  );
}

function TimelineView({ events }) {
  return (
    <div style={{ overflowX:'auto', paddingBottom:8 }}>
      <div style={{ display:'flex', gap:0, minWidth: events.length * 180 + 'px', position:'relative' }}>
        {/* line */}
        <div style={{ position:'absolute', top:20, left:20, right:20, height:2,
          background:'linear-gradient(90deg,#1F2937,#2D3748,#1F2937)' }} />
        {events.map((ev, i) => (
          <div key={i} style={{ flex:1, paddingTop:0, display:'flex', flexDirection:'column', alignItems:'center', gap:10 }}>
            {/* Dot */}
            <div style={{ width:14, height:14, borderRadius:'50%', zIndex:2, flexShrink:0,
              background: TYPE_COLORS[ev.type] || '#6B7280',
              boxShadow:`0 0 8px ${TYPE_COLORS[ev.type] || '#6B7280'}66`,
              border:'2px solid #0A0F1E' }} />
            {/* Card */}
            <div style={{ background:'rgba(255,255,255,0.03)', border:`1px solid ${TYPE_COLORS[ev.type] || '#1F2937'}33`,
              borderRadius:10, padding:'10px 12px', width:'calc(100% - 24px)', textAlign:'center' }}>
              <p style={{ fontSize:10, color: TYPE_COLORS[ev.type], fontFamily:'DM Sans,sans-serif',
                fontWeight:600, margin:'0 0 4px', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                {ev.date}
              </p>
              <p style={{ fontSize:12, color:'#D1D5DB', fontFamily:'DM Sans,sans-serif',
                margin:0, lineHeight:1.5 }}>
                {ev.event}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [alerts, setAlerts] = useState(mockAlerts);
  const [timeRange, setTimeRange] = useState('1m');

  const dismissAlert = (id) => setAlerts(a => a.filter(x => x.id !== id));

  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', gap:28 }}>
        {/* Page header */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:12 }}>
          <div>
            <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:26, fontWeight:800,
              color:'#F9FAFB', margin:'0 0 4px' }}>
              Good afternoon, {mockUser.name.split(' ')[0]} 👋
            </h1>
            <p style={{ fontSize:14, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              Your health intelligence summary · {new Date().toLocaleDateString('en-IN',{ weekday:'long', day:'numeric', month:'long' })}
            </p>
          </div>
          <button className="btn-cyan" style={{ display:'flex', alignItems:'center', gap:6 }}>
            <Zap size={14} /> Weekly Brief
          </button>
        </div>

        {/* Hero + Quick stats */}
        <div style={{ display:'grid', gridTemplateColumns:'auto 1fr', gap:24, alignItems:'start' }}
          className="dashboard-hero">
          <HealthScoreWidget
            score={mockHealthScore.score}
            lastWeek={mockHealthScore.lastWeek}
            updatedAt={mockHealthScore.updatedAt}
            confidence={mockHealthScore.confidence}
          />
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
            <QuickStat icon={Activity} label="Last Lab Report" value="May 7, 2026" sub="ABDM synced" color="#10B981" />
            <QuickStat icon={Zap} label="Wearable" value="Live sync" dot color="#10B981" />
            <QuickStat icon={Pill} label="Medication Streak" value={`${mockUser.medicationStreak} days`} sub="100% adherence" color="#00D4FF" />
            <QuickStat icon={Calendar} label="Next Checkup" value={mockUser.nextCheckup} sub="Recommended" color="#7C3AED" />
          </div>
        </div>

        {/* Risk Signal Cards */}
        <section>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
            <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
              color:'#F9FAFB', margin:0 }}>Risk Signals</h2>
            <button style={{ display:'flex', alignItems:'center', gap:4, fontSize:13,
              color:'#00D4FF', background:'none', border:'none', cursor:'pointer',
              fontFamily:'DM Sans,sans-serif' }}>
              View all <ChevronRight size={14} />
            </button>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(240px,1fr))', gap:16 }}>
            {mockRiskCards.map(card => <RiskSignalCard key={card.id} card={card} />)}
          </div>
        </section>

        {/* Alerts */}
        <section>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
                color:'#F9FAFB', margin:0 }}>Active Alerts</h2>
              {alerts.length > 0 && (
                <span style={{ background:'rgba(239,68,68,0.15)', color:'#EF4444',
                  borderRadius:20, fontSize:11, fontWeight:700, padding:'2px 8px' }}>
                  {alerts.length}
                </span>
              )}
            </div>
          </div>
          <AlertPanel alerts={alerts} onDismiss={dismissAlert} />
        </section>

        {/* Timeline */}
        <section>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
            <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
              color:'#F9FAFB', margin:0 }}>Health Timeline</h2>
            <div style={{ display:'flex', gap:4, background:'rgba(255,255,255,0.04)', borderRadius:8, padding:4 }}>
              {['1m','3m','1y'].map(r => (
                <button key={r} onClick={() => setTimeRange(r)} style={{
                  padding:'5px 12px', borderRadius:6, border:'none', cursor:'pointer',
                  background: timeRange===r ? 'rgba(0,212,255,0.12)' : 'transparent',
                  color: timeRange===r ? '#00D4FF' : '#9CA3AF',
                  fontFamily:'DM Sans,sans-serif', fontSize:12, fontWeight:500, transition:'all 0.2s',
                }}>
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div className="glass-card" style={{ padding:20 }}>
            <TimelineView events={mockTimeline} />
          </div>
        </section>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .dashboard-hero { grid-template-columns: 1fr !important; }
        }
        @media (max-width: 600px) {
          .dashboard-hero > div:last-child { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </AppShell>
  );
}
