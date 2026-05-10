import { useState } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';

export default function AlertPanel({ alerts, onDismiss }) {
  const [expanded, setExpanded] = useState({});

  const severityColors = {
    warning: { bg:'rgba(245,158,11,0.08)', border:'rgba(245,158,11,0.25)', icon:'⚠️', label:'Warning' },
    info:    { bg:'rgba(0,212,255,0.06)',   border:'rgba(0,212,255,0.2)',   icon:'ℹ️',  label:'Info' },
    danger:  { bg:'rgba(239,68,68,0.08)',   border:'rgba(239,68,68,0.3)',   icon:'🚨',  label:'Urgent' },
  };

  if (!alerts.length) return (
    <div className="glass-card" style={{ padding:28, textAlign:'center' }}>
      <p style={{ fontSize:28, margin:'0 0 8px' }}>✅</p>
      <h4 style={{ fontFamily:'Syne,sans-serif', color:'#10B981', margin:'0 0 4px' }}>No Active Alerts</h4>
      <p style={{ fontSize:13, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
        Your signals look clear. Keep it up!
      </p>
    </div>
  );

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
      {alerts.map(alert => {
        const sc = severityColors[alert.severity] || severityColors.info;
        const isExpanded = expanded[alert.id];
        return (
          <div key={alert.id} className={alert.severity === 'danger' ? 'alert-glow' : ''}
            style={{ background:sc.bg, border:`1px solid ${sc.border}`,
              borderRadius:14, padding:'16px 18px', transition:'all 0.3s' }}>
            
            {/* Header row */}
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ fontSize:18 }}>{sc.icon}</span>
                <div>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <span style={{ fontFamily:'Syne,sans-serif', fontSize:14, fontWeight:700, color:'#F9FAFB' }}>
                      {alert.signal}
                    </span>
                    <span style={{ fontSize:10, color:'#6B7280', fontFamily:'DM Sans,sans-serif' }}>
                      {alert.time}
                    </span>
                  </div>
                  <p style={{ fontSize:13, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif',
                    margin:'2px 0 0', lineHeight:1.5 }}>
                    {alert.why}
                  </p>
                </div>
              </div>
              <div style={{ display:'flex', gap:8, alignItems:'center', flexShrink:0 }}>
                <button onClick={() => setExpanded(e => ({ ...e, [alert.id]: !e[alert.id] }))}
                  style={{ background:'none', border:'none', color:'#9CA3AF', cursor:'pointer', padding:4 }}>
                  {isExpanded ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                </button>
                <button onClick={() => onDismiss(alert.id)}
                  style={{ background:'none', border:'none', color:'#6B7280', cursor:'pointer', padding:4 }}>
                  <X size={16}/>
                </button>
              </div>
            </div>

            {/* Expanded content */}
            {isExpanded && (
              <div style={{ marginTop:14, paddingTop:14, borderTop:'1px solid rgba(255,255,255,0.06)',
                display:'flex', flexDirection:'column', gap:10 }}>
                {/* Action */}
                <div style={{ background:'rgba(0,212,255,0.06)', borderRadius:10, padding:'10px 14px' }}>
                  <p style={{ fontSize:12, color:'#00D4FF', fontWeight:600, margin:'0 0 2px',
                    fontFamily:'DM Sans,sans-serif', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                    What to do
                  </p>
                  <p style={{ fontSize:13, color:'#D1D5DB', fontFamily:'DM Sans,sans-serif', margin:0, lineHeight:1.6 }}>
                    {alert.action}
                  </p>
                </div>
                {/* Counterfactual */}
                <div style={{ background:'rgba(124,58,237,0.08)', borderRadius:10, padding:'10px 14px',
                  border:'1px solid rgba(124,58,237,0.2)' }}>
                  <p style={{ fontSize:12, color:'#A78BFA', fontWeight:600, margin:'0 0 2px',
                    fontFamily:'DM Sans,sans-serif', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                    Counterfactual
                  </p>
                  <p style={{ fontSize:13, color:'#C4B5FD', fontFamily:'DM Sans,sans-serif', margin:0, lineHeight:1.6 }}>
                    {alert.counterfactual}
                  </p>
                </div>
                {/* Confidence + buttons */}
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                  <span style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif' }}>
                    Signal confidence: <strong style={{ color:'#F9FAFB' }}>{alert.confidence}%</strong>
                  </span>
                  <button onClick={() => onDismiss(alert.id)} style={{
                    background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.1)',
                    color:'#9CA3AF', padding:'6px 14px', borderRadius:8, cursor:'pointer',
                    fontFamily:'DM Sans,sans-serif', fontSize:12 }}>
                    Mark as reviewed
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
