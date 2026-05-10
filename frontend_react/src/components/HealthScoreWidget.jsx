import { useEffect, useState, useRef } from 'react';

export default function HealthScoreWidget({ score, lastWeek, updatedAt, confidence }) {
  const [displayed, setDisplayed] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    let start = 0;
    const duration = 1500;
    const step = Math.ceil(score / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= score) { setDisplayed(score); clearInterval(timer); }
      else setDisplayed(start);
    }, 16);
    return () => clearInterval(timer);
  }, [score]);

  const size = 240;
  const stroke = 14;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const progress = displayed / 100;
  const offset = circ - progress * circ;

  const ringColor = displayed < 40 ? '#10B981' : displayed < 70 ? '#F59E0B' : '#EF4444';
  const ringClass = displayed < 40 ? 'ring-safe' : displayed < 70 ? 'ring-warning' : 'ring-danger';

  const diff = score - lastWeek;
  const trendColor = diff >= 0 ? '#10B981' : '#EF4444';
  const trendArrow = diff >= 0 ? '↑' : '↓';

  return (
    <div className="glass-card" style={{
      padding: 36, display: 'flex', flexDirection: 'column', alignItems: 'center',
      gap: 16, background: 'rgba(255,255,255,0.03)', position: 'relative', overflow: 'hidden',
    }}>
      {/* Glow behind ring */}
      <div style={{
        position: 'absolute', width: 200, height: 200, borderRadius: '50%',
        background: `radial-gradient(circle, ${ringColor}18 0%, transparent 70%)`,
        top: '50%', left: '50%', transform: 'translate(-50%, -60%)',
        transition: 'background 1s ease', pointerEvents: 'none',
      }} />

      <h3 style={{ fontFamily:'Syne,sans-serif', fontSize:13, fontWeight:600,
        color:'#9CA3AF', letterSpacing:'0.12em', textTransform:'uppercase', margin:0 }}>
        Health Intelligence Score
      </h3>

      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle cx={size/2} cy={size/2} r={r}
            fill="none" stroke="#1F2937" strokeWidth={stroke} />
          {/* Progress */}
          <circle cx={size/2} cy={size/2} r={r}
            fill="none" strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={mounted ? offset : circ}
            className={ringClass}
            style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.22,1,0.36,1), stroke 0.5s' }}
          />
        </svg>

        {/* Score text */}
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4,
        }}>
          <span style={{ fontFamily:'Syne,sans-serif', fontSize:62, fontWeight:800,
            color: ringColor, lineHeight: 1,
            textShadow: `0 0 30px ${ringColor}66`,
            transition: 'color 0.5s', }}>
            {displayed}
          </span>
          <span style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif' }}>/ 100</span>
          <div style={{ display:'flex',alignItems:'center',gap:6,marginTop:4 }}>
            <span style={{ color:trendColor,fontSize:14,fontWeight:700 }}>
              {trendArrow} {Math.abs(diff)} vs last week
            </span>
          </div>
        </div>
      </div>

      <div style={{ textAlign:'center', display:'flex', flexDirection:'column', gap:4 }}>
        <p style={{ fontSize:12,color:'#9CA3AF',fontFamily:'DM Sans,sans-serif',margin:0 }}>
          {updatedAt} · {confidence}% confidence
        </p>
        <button style={{ fontSize:12,color:'#00D4FF',background:'none',border:'none',
          cursor:'pointer',fontFamily:'DM Sans,sans-serif',textDecoration:'underline' }}>
          Why is my score this? →
        </button>
      </div>
    </div>
  );
}
