import { useState } from 'react';
import AppShell from '../components/AppShell';
import { mockUser } from '../mockData';
import { Bell, Shield, Moon, Smartphone, Trash2, ToggleLeft, ToggleRight, AlertTriangle, PhoneCall } from 'lucide-react';

function ToggleRow({ label, desc, value, onChange, color = '#00D4FF' }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center',
      padding:'14px 0', borderBottom:'1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ flex:1, marginRight:24 }}>
        <p style={{ fontFamily:'DM Sans,sans-serif', fontSize:14, fontWeight:600,
          color:'#D1D5DB', margin:'0 0 2px' }}>{label}</p>
        {desc && <p style={{ fontSize:12, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>{desc}</p>}
      </div>
      <button onClick={() => onChange(!value)} style={{
        width:48, height:26, borderRadius:13,
        background: value ? `${color}44` : '#1F2937',
        border: value ? `1px solid ${color}66` : '1px solid #374151',
        cursor:'pointer', position:'relative', transition:'all 0.3s', flexShrink:0,
      }}>
        <div style={{ width:20, height:20, borderRadius:'50%',
          background: value ? color : '#6B7280',
          position:'absolute', top:2,
          left: value ? 24 : 2,
          transition:'all 0.3s',
          boxShadow: value ? `0 0 10px ${color}88` : 'none',
        }} />
      </button>
    </div>
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <div className="glass-card" style={{ padding:'22px 24px' }}>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:6 }}>
        <Icon size={18} style={{ color:'#00D4FF' }} />
        <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700, color:'#F9FAFB', margin:0 }}>
          {title}
        </h2>
      </div>
      {children}
    </div>
  );
}

export default function SettingsPage() {
  const [notifs, setNotifs] = useState({
    alerts: true, weekly: true, familyAlerts: true, marketing: false,
  });
  const [sos, setSos] = useState({
    enabled: true,
    nightOnly: true,
    contact: 'Rajesh Sharma (Father)',
    phone: '+91 98765 43210',
  });
  const [privacy, setPrivacy] = useState({
    abdm: true, wearable: true, analytics: false,
  });

  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', gap:24, maxWidth:720 }}>
        <div>
          <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:26, fontWeight:800,
            color:'#F9FAFB', margin:'0 0 4px' }}>Settings</h1>
          <p style={{ fontSize:14, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
            Manage notifications, emergency contacts, and data privacy.
          </p>
        </div>

        {/* Notifications */}
        <Section title="Notifications" icon={Bell}>
          <ToggleRow label="Health Alerts" desc="Notified when a new risk signal is detected"
            value={notifs.alerts} onChange={v => setNotifs(n=>({...n,alerts:v}))} />
          <ToggleRow label="Weekly Health Brief" desc="Every Sunday — your week in health"
            value={notifs.weekly} onChange={v => setNotifs(n=>({...n,weekly:v}))} />
          <ToggleRow label="Family Alerts" desc="Alerts for family members you're monitoring"
            value={notifs.familyAlerts} onChange={v => setNotifs(n=>({...n,familyAlerts:v}))} />
          <ToggleRow label="Product Updates" desc="News about RelayMed features" color="#7C3AED"
            value={notifs.marketing} onChange={v => setNotifs(n=>({...n,marketing:v}))} />
        </Section>

        {/* Emergency SOS */}
        <Section title="Emergency SOS" icon={AlertTriangle}>
          <p style={{ fontSize:13, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:'0 0 8px' }}>
            If a high-risk anomaly is detected, automatically notify your emergency contact.
          </p>
          <ToggleRow label="Emergency SOS Enabled" desc="Auto-notify on critical anomalies"
            value={sos.enabled} onChange={v => setSos(s=>({...s,enabled:v}))} color="#EF4444" />
          <ToggleRow label="Night Mode Only" desc="Only trigger between 10 PM – 6 AM"
            value={sos.nightOnly} onChange={v => setSos(s=>({...s,nightOnly:v}))} color="#F59E0B" />

          {/* Emergency contact */}
          <div style={{ marginTop:14, padding:'14px 16px', background:'rgba(239,68,68,0.06)',
            border:'1px solid rgba(239,68,68,0.2)', borderRadius:12 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <PhoneCall size={16} style={{ color:'#EF4444' }} />
                <div>
                  <p style={{ fontFamily:'DM Sans,sans-serif', fontSize:14, fontWeight:600,
                    color:'#D1D5DB', margin:'0 0 2px' }}>{sos.contact}</p>
                  <p style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:0 }}>{sos.phone}</p>
                </div>
              </div>
              <button className="btn-ghost" style={{ fontSize:12, padding:'6px 12px' }}>Edit</button>
            </div>
          </div>
        </Section>

        {/* Privacy & Data */}
        <Section title="Privacy & Data Control" icon={Shield}>
          <p style={{ fontSize:13, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:'0 0 8px' }}>
            DPDP compliant. Revoke any data source at any time.
          </p>
          <ToggleRow label="ABDM / ABHA Data Access" desc="Health records from Ayushman Bharat"
            value={privacy.abdm} onChange={v => setPrivacy(p=>({...p,abdm:v}))} />
          <ToggleRow label="Wearable Data" desc="Apple Health, Fitbit sync"
            value={privacy.wearable} onChange={v => setPrivacy(p=>({...p,wearable:v}))} />
          <ToggleRow label="Anonymous Analytics" desc="Help improve RelayMed (no personal data)" color="#7C3AED"
            value={privacy.analytics} onChange={v => setPrivacy(p=>({...p,analytics:v}))} />

          <div style={{ marginTop:14, display:'flex', gap:10, flexWrap:'wrap' }}>
            <button className="btn-ghost" style={{ fontSize:12, display:'flex', alignItems:'center', gap:6 }}>
              <Smartphone size={13}/> Export my data
            </button>
            <button style={{ background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.25)',
              color:'#EF4444', padding:'8px 16px', borderRadius:8, cursor:'pointer',
              fontFamily:'DM Sans,sans-serif', fontSize:12, display:'flex', alignItems:'center', gap:6 }}>
              <Trash2 size={13}/> Delete account & data
            </button>
          </div>
        </Section>

        {/* Account info */}
        <div className="glass-card" style={{ padding:'18px 24px' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
            <div>
              <p style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700,
                color:'#F9FAFB', margin:'0 0 4px' }}>{mockUser.name}</p>
              <p style={{ fontSize:13, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                {mockUser.abhaId}
              </p>
            </div>
            <span style={{ background:'rgba(16,185,129,0.1)', border:'1px solid rgba(16,185,129,0.25)',
              color:'#10B981', fontSize:11, fontWeight:700, padding:'4px 10px', borderRadius:6,
              fontFamily:'DM Sans,sans-serif' }}>
              DPDP Verified
            </span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
