import { useState } from 'react';
import AppShell from '../components/AppShell';
import { mockUser, mockFamily } from '../mockData';
import { AlertTriangle, CheckCircle, Bell, UserPlus, Link2 } from 'lucide-react';

const SCORE_COLOR = (s) => s >= 80 ? '#10B981' : s >= 55 ? '#F59E0B' : '#EF4444';

function ScoreRing({ score, size = 80 }) {
  const stroke = 7;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const color = SCORE_COLOR(score);
  return (
    <div style={{ position:'relative', width:size, height:size, flexShrink:0 }}>
      <svg width={size} height={size} style={{ transform:'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1F2937" strokeWidth={stroke}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" strokeWidth={stroke}
          strokeLinecap="round" strokeDasharray={circ}
          strokeDashoffset={circ - (score/100)*circ}
          stroke={color} style={{ filter:`drop-shadow(0 0 5px ${color}88)`, transition:'stroke-dashoffset 1s ease' }}/>
      </svg>
      <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center' }}>
        <span style={{ fontFamily:'Syne,sans-serif', fontSize:size*0.22, fontWeight:800, color }}>{score}</span>
      </div>
    </div>
  );
}

function FamilyCard({ member }) {
  const [alertPref, setAlertPref] = useState(true);
  const color = SCORE_COLOR(member.healthScore);

  return (
    <div className="glass-card" style={{ padding:22, display:'flex', flexDirection:'column', gap:16 }}>
      {/* Top row */}
      <div style={{ display:'flex', gap:16, alignItems:'center' }}>
        <div style={{ position:'relative' }}>
          <div style={{ width:56, height:56, borderRadius:'50%',
            background:`linear-gradient(135deg, ${color}33, ${color}11)`,
            border:`2px solid ${color}44`,
            display:'flex', alignItems:'center', justifyContent:'center',
            fontSize:22, fontWeight:700, color, fontFamily:'Syne,sans-serif' }}>
            {member.name.charAt(0)}
          </div>
          {member.alerts > 0 && (
            <span style={{ position:'absolute', top:-4, right:-4, background:'#EF4444',
              color:'white', borderRadius:'50%', width:18, height:18, fontSize:10,
              display:'flex', alignItems:'center', justifyContent:'center', fontWeight:700 }}>
              {member.alerts}
            </span>
          )}
        </div>
        <div style={{ flex:1 }}>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <h3 style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700, color:'#F9FAFB', margin:0 }}>
              {member.name}
            </h3>
            <span style={{ background:'rgba(0,212,255,0.1)', border:'1px solid rgba(0,212,255,0.2)',
              color:'#00D4FF', fontSize:10, borderRadius:6, padding:'2px 7px', fontWeight:600,
              fontFamily:'DM Sans,sans-serif' }}>
              Shared ✓
            </span>
          </div>
          <p style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:'2px 0 0' }}>
            {member.relation} · {member.age} yrs · Synced {member.lastSync}
          </p>
        </div>
        <ScoreRing score={member.healthScore} />
      </div>

      {/* Signals */}
      <div style={{ display:'flex', gap:8 }}>
        {member.signals.map(sig => {
          const sc = sig.status === 'safe' ? '#10B981' : sig.status === 'warning' ? '#F59E0B' : '#EF4444';
          return (
            <div key={sig.label} style={{ flex:1, background:`${sc}11`, border:`1px solid ${sc}33`,
              borderRadius:8, padding:'8px 10px', textAlign:'center' }}>
              <span style={{ fontSize:18 }}>{sig.icon}</span>
              <p style={{ fontSize:10, color:sc, margin:'4px 0 0', fontFamily:'DM Sans,sans-serif', fontWeight:600 }}>
                {sig.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Shared risks */}
      {member.sharedRisks.length > 0 && (
        <div style={{ background:'rgba(124,58,237,0.08)', border:'1px solid rgba(124,58,237,0.2)',
          borderRadius:8, padding:'8px 12px' }}>
          <p style={{ fontSize:11, color:'#A78BFA', fontFamily:'DM Sans,sans-serif', margin:0 }}>
            🧬 Shared risk factors: {member.sharedRisks.join(', ')}
          </p>
        </div>
      )}

      {/* Alert pref */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <Bell size={13} style={{ color:'#9CA3AF' }} />
          <span style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif' }}>
            Notify me on alerts
          </span>
        </div>
        <button onClick={() => setAlertPref(v => !v)} style={{
          width:42, height:24, borderRadius:12,
          background: alertPref ? 'rgba(0,212,255,0.3)' : '#1F2937',
          border: alertPref ? '1px solid rgba(0,212,255,0.4)' : '1px solid #374151',
          cursor:'pointer', position:'relative', transition:'all 0.3s',
        }}>
          <div style={{ width:18, height:18, borderRadius:'50%',
            background: alertPref ? '#00D4FF' : '#6B7280',
            position:'absolute', top:2,
            left: alertPref ? 20 : 2,
            transition:'all 0.3s',
            boxShadow: alertPref ? '0 0 8px rgba(0,212,255,0.6)' : 'none',
          }} />
        </button>
      </div>
    </div>
  );
}

export default function FamilyGuardianPage() {
  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', gap:28 }}>
        {/* Header */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:12 }}>
          <div>
            <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:26, fontWeight:800,
              color:'#F9FAFB', margin:'0 0 6px' }}>
              Family Health Guardian
            </h1>
            <p style={{ fontSize:14, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              Monitor your loved ones with their consent. One-tap revocation anytime.
            </p>
          </div>
          <button className="btn-cyan" style={{ display:'flex', alignItems:'center', gap:8 }}>
            <UserPlus size={15} /> Add Family Member
          </button>
        </div>

        {/* Family overview bar */}
        <div className="glass-card" style={{ padding:'18px 24px' }}>
          <div style={{ display:'flex', gap:24, flexWrap:'wrap', alignItems:'center' }}>
            <div>
              <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif',
                margin:'0 0 2px', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                Members Monitoring
              </p>
              <p style={{ fontFamily:'Syne,sans-serif', fontSize:24, fontWeight:800,
                color:'#F9FAFB', margin:0 }}>
                {mockFamily.length}
              </p>
            </div>
            <div style={{ width:1, height:40, background:'#1F2937' }} />
            <div>
              <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif',
                margin:'0 0 2px', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                Active Alerts
              </p>
              <p style={{ fontFamily:'Syne,sans-serif', fontSize:24, fontWeight:800,
                color:'#EF4444', margin:0 }}>
                {mockFamily.reduce((a, m) => a + m.alerts, 0)}
              </p>
            </div>
            <div style={{ width:1, height:40, background:'#1F2937' }} />
            <div>
              <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif',
                margin:'0 0 2px', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                Avg Family Score
              </p>
              <p style={{ fontFamily:'Syne,sans-serif', fontSize:24, fontWeight:800,
                color:'#F59E0B', margin:0 }}>
                {Math.round(mockFamily.reduce((a,m) => a+m.healthScore,0)/mockFamily.length)}
              </p>
            </div>
            <div style={{ marginLeft:'auto' }}>
              <div style={{ background:'rgba(124,58,237,0.1)', border:'1px solid rgba(124,58,237,0.25)',
                borderRadius:10, padding:'10px 16px' }}>
                <p style={{ fontSize:12, color:'#A78BFA', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                  🧬 Your father and you share 3 common risk factors
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Family Cards */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(320px,1fr))', gap:18 }}>
          {mockFamily.map(m => <FamilyCard key={m.id} member={m} />)}

          {/* Add member card */}
          <div className="glass-card" style={{ padding:22, display:'flex', flexDirection:'column',
            alignItems:'center', justifyContent:'center', gap:16, minHeight:220,
            border:'2px dashed rgba(255,255,255,0.08)', cursor:'pointer',
            background:'rgba(255,255,255,0.01)' }}>
            <div style={{ width:56, height:56, borderRadius:'50%',
              background:'rgba(0,212,255,0.08)', border:'2px dashed rgba(0,212,255,0.3)',
              display:'flex', alignItems:'center', justifyContent:'center' }}>
              <UserPlus size={22} style={{ color:'#00D4FF' }} />
            </div>
            <div style={{ textAlign:'center' }}>
              <p style={{ fontFamily:'Syne,sans-serif', fontSize:15, fontWeight:600,
                color:'#9CA3AF', margin:'0 0 4px' }}>Add Family Member</p>
              <p style={{ fontSize:12, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                Sends a consent request via their ABHA ID
              </p>
            </div>
          </div>
        </div>

        {/* Emergency settings */}
        <div className="glass-card" style={{ padding:24 }}>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:16 }}>
            <AlertTriangle size={18} style={{ color:'#F59E0B' }} />
            <h3 style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700,
              color:'#F9FAFB', margin:0 }}>Emergency Notification Rules</h3>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {[
              { rule:"If Dad's heart rate stays elevated for more than 2 hours", active:true },
              { rule:"If any member has SpO₂ below 90% between 10 PM – 6 AM", active:true },
              { rule:"If Mom misses medication for 3 consecutive days", active:false },
            ].map((r, i) => (
              <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center',
                padding:'12px 16px', background:'rgba(255,255,255,0.03)', borderRadius:10,
                border:'1px solid rgba(255,255,255,0.06)' }}>
                <p style={{ fontSize:13, color:'#D1D5DB', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                  🔔 {r.rule}
                </p>
                <div style={{ display:'flex', alignItems:'center', gap:8, flexShrink:0, marginLeft:16 }}>
                  {r.active ? <CheckCircle size={14} style={{ color:'#10B981' }}/> : null}
                  <span style={{ fontSize:11, fontWeight:600,
                    color: r.active ? '#10B981' : '#6B7280' }}>
                    {r.active ? 'Active' : 'Off'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
