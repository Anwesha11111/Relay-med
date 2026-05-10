import { useState, useRef } from 'react';
import AppShell from '../components/AppShell';
import { TrustBadge } from '../components/RiskSignalCard';
import { mockUser, mockConnectedSources } from '../mockData';
import { Upload, RefreshCw, Download, CheckCircle, XCircle, Link2 } from 'lucide-react';

function SourceCard({ source }) {
  const [connecting, setConnecting] = useState(false);
  const statusColor = source.status === 'connected' ? '#10B981'
    : source.status === 'disconnected' ? '#EF4444' : '#6B7280';
  const statusIcon = source.status === 'connected' ? <CheckCircle size={14}/>
    : source.status === 'disconnected' ? <XCircle size={14}/> : <Link2 size={14}/>;

  const handleConnect = async () => {
    if (source.status === 'connected') return;
    setConnecting(true);
    await new Promise(r => setTimeout(r, 1400));
    setConnecting(false);
  };

  return (
    <div className="glass-card" style={{ padding:'18px 20px', display:'flex', alignItems:'center', gap:16 }}>
      <div style={{ width:48, height:48, borderRadius:12,
        background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)',
        display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, flexShrink:0 }}>
        {source.icon}
      </div>
      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:3 }}>
          <h4 style={{ fontFamily:'Syne,sans-serif', fontSize:14, fontWeight:700,
            color:'#F9FAFB', margin:0 }}>{source.name}</h4>
          <TrustBadge level={source.trust} />
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:6 }}>
          <span style={{ color:statusColor, display:'flex', alignItems:'center' }}>{statusIcon}</span>
          <span style={{ fontSize:12, color:statusColor, fontFamily:'DM Sans,sans-serif', fontWeight:500 }}>
            {source.status.charAt(0).toUpperCase() + source.status.slice(1)}
          </span>
          <span style={{ fontSize:12, color:'#6B7280', fontFamily:'DM Sans,sans-serif' }}>
            · Last: {source.lastSync} · {source.records} records
          </span>
        </div>
      </div>
      <div style={{ display:'flex', gap:8, flexShrink:0 }}>
        {source.status === 'connected' && (
          <button style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)',
            color:'#9CA3AF', padding:'7px', borderRadius:8, cursor:'pointer', display:'flex',
            transition:'all 0.2s' }}>
            <RefreshCw size={14}/>
          </button>
        )}
        <button onClick={handleConnect} style={{
          background: source.status === 'connected' ? 'rgba(239,68,68,0.1)' : 'rgba(0,212,255,0.1)',
          border: source.status === 'connected' ? '1px solid rgba(239,68,68,0.3)' : '1px solid rgba(0,212,255,0.3)',
          color: source.status === 'connected' ? '#EF4444' : '#00D4FF',
          padding:'7px 14px', borderRadius:8, cursor:'pointer',
          fontFamily:'DM Sans,sans-serif', fontSize:12, fontWeight:500, transition:'all 0.2s',
          display:'flex', alignItems:'center', gap:6 }}>
          {connecting ? <><RefreshCw size={12} style={{ animation:'spin 0.8s linear infinite' }} />Connecting…</>
            : source.status === 'connected' ? 'Revoke' : 'Connect'}
        </button>
      </div>
    </div>
  );
}

const TRUST_INFO = {
  HIGH:   'Lab reports, ABDM records — highest clinical reliability.',
  MEDIUM: 'Wearable & fitness app data — good for trends, not diagnostics.',
  LOW:    'Manual entries — useful context, lowest verification confidence.',
};

export default function ReportsPage() {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState([
    { name:'Blood_Panel_May7_2026.pdf', date:'May 7, 2026', trust:'HIGH', parsed:true },
    { name:'Radiology_Chest_Apr2026.pdf', date:'Apr 14, 2026', trust:'HIGH', parsed:true },
  ]);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.pdf')) return;
    setUploading(true);
    await new Promise(r => setTimeout(r, 2000));
    setUploaded(u => [{ name:file.name, date:'Today', trust:'LOW', parsed:true }, ...u]);
    setUploading(false);
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', gap:28 }}>
        {/* Header */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:12 }}>
          <div>
            <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:26, fontWeight:800,
              color:'#F9FAFB', margin:'0 0 4px' }}>Reports & Data Sources</h1>
            <p style={{ fontSize:14, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              Manage your connected health data. Each source carries a trust weight that influences your score.
            </p>
          </div>
          <button className="btn-cyan" style={{ display:'flex', alignItems:'center', gap:6 }}>
            <Download size={14}/> Export History
          </button>
        </div>

        {/* Trust explanation */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14 }} className="trust-grid">
          {Object.entries(TRUST_INFO).map(([level, desc]) => {
            const colors = { HIGH:'#00D4FF', MEDIUM:'#F59E0B', LOW:'#EF4444' };
            const c = colors[level];
            return (
              <div key={level} style={{ background:`${c}08`, border:`1px solid ${c}22`, borderRadius:12, padding:'14px 16px' }}>
                <TrustBadge level={level} />
                <p style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:'8px 0 0', lineHeight:1.6 }}>
                  {desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Upload zone */}
        <div>
          <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
            color:'#F9FAFB', margin:'0 0 14px' }}>Upload Lab Report</h2>
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            style={{
              border:`2px dashed ${dragOver ? '#00D4FF' : 'rgba(255,255,255,0.12)'}`,
              borderRadius:16, padding:'40px 24px', textAlign:'center', cursor:'pointer',
              background: dragOver ? 'rgba(0,212,255,0.05)' : 'rgba(255,255,255,0.02)',
              transition:'all 0.3s',
              boxShadow: dragOver ? '0 0 24px rgba(0,212,255,0.15)' : 'none',
            }}>
            <input ref={fileRef} type="file" accept=".pdf" style={{ display:'none' }}
              onChange={e => handleFile(e.target.files[0])} />
            {uploading ? (
              <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:12 }}>
                <div style={{ width:44, height:44, border:'3px solid rgba(0,212,255,0.2)',
                  borderTopColor:'#00D4FF', borderRadius:'50%', animation:'spin 0.8s linear infinite' }} />
                <p style={{ color:'#00D4FF', fontFamily:'DM Sans,sans-serif', margin:0, fontSize:14 }}>
                  Parsing report with OCR…
                </p>
              </div>
            ) : (
              <>
                <Upload size={36} style={{ color: dragOver ? '#00D4FF' : '#4B5563', marginBottom:12 }} />
                <p style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700,
                  color:'#D1D5DB', margin:'0 0 6px' }}>
                  Drop your lab report PDF here
                </p>
                <p style={{ fontSize:13, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                  or click to browse · OCR auto-parses values
                </p>
              </>
            )}
          </div>
        </div>

        {/* Uploaded reports */}
        {uploaded.length > 0 && (
          <div>
            <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
              color:'#F9FAFB', margin:'0 0 14px' }}>Uploaded Reports</h2>
            <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
              {uploaded.map((doc, i) => (
                <div key={i} className="glass-card"
                  style={{ padding:'14px 18px', display:'flex', alignItems:'center', gap:14 }}>
                  <span style={{ fontSize:24 }}>📄</span>
                  <div style={{ flex:1 }}>
                    <p style={{ fontFamily:'DM Sans,sans-serif', fontSize:14, fontWeight:600,
                      color:'#F9FAFB', margin:'0 0 2px' }}>{doc.name}</p>
                    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                      <span style={{ fontSize:12, color:'#6B7280', fontFamily:'DM Sans,sans-serif' }}>
                        {doc.date}
                      </span>
                      <TrustBadge level={doc.trust} />
                      {doc.parsed && (
                        <span style={{ fontSize:11, color:'#10B981', fontFamily:'DM Sans,sans-serif',
                          display:'flex', alignItems:'center', gap:4 }}>
                          <CheckCircle size={11}/> Parsed
                        </span>
                      )}
                    </div>
                  </div>
                  <button className="btn-ghost" style={{ fontSize:12, padding:'6px 12px' }}>View</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Connected sources */}
        <div>
          <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:700,
            color:'#F9FAFB', margin:'0 0 14px' }}>Connected Sources</h2>
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {mockConnectedSources.map(s => <SourceCard key={s.name} source={s} />)}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width:700px) { .trust-grid { grid-template-columns:1fr !important; } }
        @keyframes spin { 100% { transform:rotate(360deg); } }
      `}</style>
    </AppShell>
  );
}
