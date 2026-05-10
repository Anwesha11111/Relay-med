import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RelayMedLogo } from '../components/Logo';
import { Shield, Eye, EyeOff } from 'lucide-react';

// Animated Particle Network
function ParticleCanvas() {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    let animId;
    const W = canvas.width = window.innerWidth;
    const H = canvas.height = window.innerHeight;

    const nodes = Array.from({ length: 60 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 1,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      nodes.forEach(n => {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
      });
      // Connections
      nodes.forEach((a, i) => {
        nodes.slice(i + 1).forEach(b => {
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            const alpha = (1 - dist / 130) * 0.35;
            const g = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
            g.addColorStop(0, `rgba(0,212,255,${alpha})`);
            g.addColorStop(1, `rgba(124,58,237,${alpha})`);
            ctx.strokeStyle = g;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        });
      });
      // Nodes
      nodes.forEach(n => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0,212,255,0.6)';
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#00D4FF';
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animId);
  }, []);

  return <canvas ref={ref} style={{ position:'fixed', inset:0, zIndex:0, opacity:0.6 }} />;
}

// ECG Line SVG
function EcgLine() {
  return (
    <div style={{ position:'fixed', bottom:0, left:0, right:0, height:60, zIndex:1, opacity:0.5, overflow:'hidden' }}>
      <svg viewBox="0 0 1440 60" preserveAspectRatio="none" style={{ width:'100%', height:'100%' }}>
        <path className="ecg-line"
          d="M0,30 L200,30 L220,30 L230,5 L240,55 L250,30 L260,30 L280,30 L
             500,30 L520,30 L530,5 L540,55 L550,30 L560,30 L580,30 L
             800,30 L820,30 L830,5 L840,55 L850,30 L860,30 L880,30 L
             1100,30 L1120,30 L1130,5 L1140,55 L1150,30 L1440,30"
          stroke="#00D4FF" strokeWidth="1.5" fill="none" strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

export default function LoginPage() {
  const [tab, setTab] = useState('abha'); // abha | oauth
  const [abhaId, setAbhaId] = useState('');
  const [showId, setShowId] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    await new Promise(r => setTimeout(r, 1800));
    localStorage.setItem('relaymed_auth', 'mock_session');
    navigate('/dashboard');
  };

  const handleOAuth = async (provider) => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    localStorage.setItem('relaymed_auth', 'mock_session');
    navigate('/dashboard');
  };

  return (
    <div style={{ minHeight:'100vh', background:'#0A0F1E', display:'flex', flexDirection:'column',
      alignItems:'center', justifyContent:'center', position:'relative', overflow:'hidden' }}>
      
      <ParticleCanvas />
      <EcgLine />

      {/* Grid overlay */}
      <div className="grid-bg" style={{ position:'fixed', inset:0, zIndex:0 }} />

      {/* Language selector */}
      <div style={{ position:'fixed', top:20, right:24, display:'flex', gap:6, zIndex:10 }}>
        {['EN','हिं','ಕನ್ನಡ','தமிழ்'].map(l => (
          <button key={l} style={{ background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.1)',
            color:'#9CA3AF', padding:'4px 10px', borderRadius:6, fontSize:11,
            cursor:'pointer', fontFamily:'DM Sans,sans-serif' }}>
            {l}
          </button>
        ))}
      </div>

      {/* Main card */}
      <div style={{ position:'relative', zIndex:10, width:'100%', maxWidth:440, padding:'0 20px' }}>
        <div className="glass-card gradient-border" style={{ padding:'40px 36px' }}>
          {/* Logo + tagline */}
          <div style={{ textAlign:'center', marginBottom:32 }}>
            <div style={{ display:'flex', justifyContent:'center', marginBottom:16 }}>
              <RelayMedLogo size="lg" />
            </div>
            <p style={{ fontFamily:'DM Sans,sans-serif', fontSize:15, color:'#9CA3AF',
              margin:0, letterSpacing:'0.02em' }}>
              Know before it happens
            </p>
          </div>

          {/* Tabs */}
          <div style={{ display:'flex', gap:0, background:'rgba(255,255,255,0.04)',
            borderRadius:10, padding:4, marginBottom:24 }}>
            {['abha','oauth'].map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                flex:1, padding:'8px', borderRadius:8, border:'none',
                background: tab===t ? 'rgba(0,212,255,0.12)' : 'transparent',
                color: tab===t ? '#00D4FF' : '#9CA3AF',
                fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:500, cursor:'pointer',
                borderBottom: tab===t ? '2px solid #00D4FF' : '2px solid transparent',
                transition:'all 0.2s',
              }}>
                {t==='abha' ? 'ABHA ID' : 'Google / Apple'}
              </button>
            ))}
          </div>

          {tab === 'abha' ? (
            <form onSubmit={handleLogin} style={{ display:'flex', flexDirection:'column', gap:16 }}>
              <div>
                <label style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif',
                  fontWeight:500, display:'block', marginBottom:6 }}>
                  Ayushman Bharat Health ID
                </label>
                <div style={{ position:'relative' }}>
                  <input
                    type={showId ? 'text' : 'password'}
                    className="input-dark"
                    placeholder="XX-XXXX-XXXX-XXXX"
                    value={abhaId}
                    onChange={e => setAbhaId(e.target.value)}
                    style={{ paddingRight:44 }}
                  />
                  <button type="button" onClick={() => setShowId(v => !v)}
                    style={{ position:'absolute', right:12, top:'50%', transform:'translateY(-50%)',
                      background:'none', border:'none', color:'#6B7280', cursor:'pointer' }}>
                    {showId ? <EyeOff size={16}/> : <Eye size={16}/>}
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}
                style={{ width:'100%', position:'relative', overflow:'hidden' }}>
                {loading ? (
                  <span style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
                    <div style={{ width:16, height:16, border:'2px solid rgba(255,255,255,0.3)',
                      borderTopColor:'white', borderRadius:'50%',
                      animation:'spin 0.8s linear infinite' }} />
                    Connecting…
                  </span>
                ) : 'Continue with ABHA ID'}
              </button>

              <button type="button" style={{ textAlign:'center', background:'none', border:'none',
                color:'#00D4FF', fontSize:13, cursor:'pointer', fontFamily:'DM Sans,sans-serif',
                textDecoration:'underline' }}>
                + Add family member
              </button>
            </form>
          ) : (
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <button onClick={() => handleOAuth('google')} style={{
                display:'flex', alignItems:'center', justifyContent:'center', gap:12,
                width:'100%', padding:'13px', borderRadius:10,
                background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.12)',
                color:'#F9FAFB', fontFamily:'DM Sans,sans-serif', fontSize:14, fontWeight:500,
                cursor:'pointer', transition:'all 0.2s' }}>
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </button>
              <button onClick={() => handleOAuth('apple')} style={{
                display:'flex', alignItems:'center', justifyContent:'center', gap:12,
                width:'100%', padding:'13px', borderRadius:10,
                background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.12)',
                color:'#F9FAFB', fontFamily:'DM Sans,sans-serif', fontSize:14, fontWeight:500,
                cursor:'pointer', transition:'all 0.2s' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                  <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.7 9.05 7.39c1.28.07 2.18.74 2.92.8 1.1-.22 2.16-.89 3.38-.84 1.44.07 2.52.61 3.22 1.54-2.96 1.77-2.25 5.67.28 6.77-.62 1.6-1.42 3.17-1.8 4.62zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                </svg>
                Continue with Apple
              </button>
              <p style={{ textAlign:'center', fontSize:12, color:'#6B7280',
                fontFamily:'DM Sans,sans-serif', margin:0 }}>
                + Add family member after sign in
              </p>
            </div>
          )}
        </div>

        {/* Privacy badge */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8,
          marginTop:20, padding:'10px 16px', borderRadius:10,
          background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.06)' }}>
          <Shield size={14} style={{ color:'#10B981' }} />
          <span style={{ fontSize:12, color:'#6B7280', fontFamily:'DM Sans,sans-serif' }}>
            DPDP Compliant &nbsp;|&nbsp; Your data, your control
          </span>
        </div>
      </div>

      <style>{`@keyframes spin { 100% { transform:rotate(360deg); } }`}</style>
    </div>
  );
}
