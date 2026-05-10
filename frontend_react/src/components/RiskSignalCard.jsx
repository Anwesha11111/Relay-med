import { useEffect, useRef } from 'react';

// Mini sparkline rendered on canvas
function Sparkline({ data, color }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current || !data?.length) return;
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const min = Math.min(...data), max = Math.max(...data);
    const range = max - min || 1;
    const points = data.map((v, i) => ({
      x: (i / (data.length - 1)) * (w - 4) + 2,
      y: h - ((v - min) / range) * (h - 8) - 4,
    }));
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, color + '66');
    grad.addColorStop(1, color);
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();
    // Fill area under curve
    ctx.lineTo(points[points.length-1].x, h);
    ctx.lineTo(points[0].x, h);
    ctx.closePath();
    const fillGrad = ctx.createLinearGradient(0, 0, 0, h);
    fillGrad.addColorStop(0, color + '22');
    fillGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = fillGrad;
    ctx.fill();
  }, [data, color]);
  return <canvas ref={ref} width={120} height={40} style={{ display:'block' }} />;
}

function TrustBadge({ level }) {
  const cfg = {
    HIGH:   { bg:'rgba(0,212,255,0.12)', color:'#00D4FF', border:'rgba(0,212,255,0.3)' },
    MEDIUM: { bg:'rgba(245,158,11,0.12)', color:'#F59E0B', border:'rgba(245,158,11,0.3)' },
    LOW:    { bg:'rgba(239,68,68,0.12)',  color:'#EF4444', border:'rgba(239,68,68,0.3)' },
  };
  const c = cfg[level] || cfg.MEDIUM;
  return (
    <span className="tooltip" data-tip={`Data reliability: ${level}`} style={{
      background:c.bg, color:c.color, border:`1px solid ${c.border}`,
      borderRadius:6, fontSize:10, fontWeight:700, padding:'2px 7px',
      letterSpacing:'0.08em', fontFamily:'DM Sans,sans-serif',
    }}>
      {level}
    </span>
  );
}

const STATUS_COLORS = {
  safe:    { text:'#10B981', bg:'rgba(16,185,129,0.1)', border:'rgba(16,185,129,0.2)' },
  warning: { text:'#F59E0B', bg:'rgba(245,158,11,0.1)',  border:'rgba(245,158,11,0.2)' },
  danger:  { text:'#EF4444', bg:'rgba(239,68,68,0.1)',   border:'rgba(239,68,68,0.2)' },
};

export { TrustBadge };

export default function RiskSignalCard({ card }) {
  const sc = STATUS_COLORS[card.statusLevel] || STATUS_COLORS.safe;
  const sparkColor = card.statusLevel === 'safe' ? '#10B981'
    : card.statusLevel === 'danger' ? '#EF4444' : '#F59E0B';
  const trendIcon = card.trend === 'up' ? '↑' : card.trend === 'down' ? '↓' : '→';
  const trendColor = card.id === 'sleep'
    ? (card.trend === 'down' ? '#EF4444' : '#10B981')
    : (card.trend === 'up' ? '#10B981' : '#EF4444');

  return (
    <div className="glass-card" style={{ padding:20, display:'flex', flexDirection:'column', gap:14 }}>
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontSize:22 }}>{card.icon}</span>
          <div>
            <h4 style={{ fontFamily:'Syne,sans-serif', fontSize:14, fontWeight:700,
              color:'#F9FAFB', margin:0 }}>{card.title}</h4>
            <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              Last: {card.lastUpdated}
            </p>
          </div>
        </div>
        <span style={{ background:sc.bg, color:sc.text, border:`1px solid ${sc.border}`,
          borderRadius:8, fontSize:11, fontWeight:600, padding:'4px 10px',
          fontFamily:'DM Sans,sans-serif' }}>
          {card.status}
        </span>
      </div>

      {/* Value + Trend */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <span style={{ fontFamily:'Syne,sans-serif', fontSize:28, fontWeight:800, color:'#F9FAFB' }}>
          {card.value.split('/')[0]}
          <span style={{ fontSize:14, color:'#6B7280' }}>/100</span>
        </span>
        <span style={{ fontSize:13, fontWeight:600, color:trendColor }}>
          {trendIcon} {card.trendLabel}
        </span>
      </div>

      {/* Sparkline */}
      <Sparkline data={card.sparkline} color={sparkColor} />

      {/* Footer */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <TrustBadge level={card.confidence >= 85 ? 'HIGH' : card.confidence >= 70 ? 'MEDIUM' : 'LOW'} />
        <span style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif' }}>
          {card.confidence}% confidence
        </span>
      </div>
    </div>
  );
}
