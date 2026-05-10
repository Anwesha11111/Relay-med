import { useState, useMemo } from 'react';
import AppShell from '../components/AppShell';
import { mockUser } from '../mockData';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts';
import { Sliders, Share2, Info } from 'lucide-react';

const DEFAULTS = { steps: 6000, sleep: 6, medication: 70, stress: 5, diet: 5 };

function calcProjected(inputs, months) {
  const base = 72;
  const stepsBonus  = ((inputs.steps - 4000) / 8000) * 12;
  const sleepBonus  = ((inputs.sleep - 5) / 3) * 14;
  const medBonus    = ((inputs.medication - 50) / 50) * 8;
  const stressBonus = ((5 - inputs.stress) / 4) * 6;
  const dietBonus   = ((inputs.diet - 3) / 7) * 10;
  const monthlyGain = (stepsBonus + sleepBonus + medBonus + stressBonus + dietBonus) / 6;
  return Math.min(99, Math.max(30, Math.round(base + monthlyGain * months)));
}

function SliderInput({ label, min, max, step = 1, value, onChange, unit, icon, description }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <span style={{ fontSize:18 }}>{icon}</span>
          <div>
            <span style={{ fontFamily:'DM Sans,sans-serif', fontSize:13, fontWeight:600, color:'#D1D5DB' }}>
              {label}
            </span>
            <p style={{ fontSize:11, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              {description}
            </p>
          </div>
        </div>
        <span style={{ fontFamily:'Syne,sans-serif', fontSize:18, fontWeight:800, color:'#00D4FF',
          minWidth:60, textAlign:'right' }}>
          {value.toLocaleString()}{unit}
        </span>
      </div>
      <div style={{ position:'relative', height:6, background:'#1F2937', borderRadius:3 }}>
        <div style={{ position:'absolute', left:0, width:`${pct}%`, height:'100%',
          background:'linear-gradient(90deg,#7C3AED,#00D4FF)', borderRadius:3,
          transition:'width 0.2s', boxShadow:'0 0 8px rgba(0,212,255,0.4)' }} />
        <input type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{ position:'absolute', inset:0, width:'100%', opacity:0, cursor:'pointer', height:'100%' }} />
        <div style={{ position:'absolute', top:'50%', left:`${pct}%`, transform:'translate(-50%,-50%)',
          width:16, height:16, borderRadius:'50%', background:'#00D4FF',
          border:'2px solid #0A0F1E', pointerEvents:'none',
          boxShadow:'0 0 10px rgba(0,212,255,0.6)', transition:'left 0.2s' }} />
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', fontSize:10, color:'#4B5563',
        fontFamily:'DM Sans,sans-serif' }}>
        <span>{min.toLocaleString()}{unit}</span><span>{max.toLocaleString()}{unit}</span>
      </div>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:'#111827', border:'1px solid rgba(0,212,255,0.2)', borderRadius:10,
      padding:'10px 14px', fontFamily:'DM Sans,sans-serif' }}>
      <p style={{ color:'#9CA3AF', fontSize:11, margin:'0 0 6px' }}>{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color:p.color, fontSize:14, fontWeight:700, margin:0 }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};

export default function TrajectorySimulatorPage() {
  const [inputs, setInputs] = useState(DEFAULTS);
  const [horizon, setHorizon] = useState('3m');

  const months = horizon === '3m' ? 3 : 6;

  const chartData = useMemo(() => {
    const labels = ['Now', 'Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6'];
    return labels.slice(0, months + 1).map((label, i) => ({
      label,
      Baseline: 72,
      Projected: i === 0 ? 72 : calcProjected(inputs, i),
    }));
  }, [inputs, months]);

  const finalScore = chartData[chartData.length - 1].Projected;
  const gain = finalScore - 72;
  const gainColor = gain > 0 ? '#10B981' : gain < 0 ? '#EF4444' : '#9CA3AF';

  const set = (k) => (v) => setInputs(i => ({ ...i, [k]: v }));

  // Key impact calc
  const impacts = [
    { label:'Sleep improvement', delta: Math.round(((inputs.sleep - DEFAULTS.sleep) / 3) * 14) },
    { label:'Step count change',  delta: Math.round(((inputs.steps - DEFAULTS.steps) / 8000) * 12) },
    { label:'Medication adherence', delta: Math.round(((inputs.medication - DEFAULTS.medication) / 50) * 8) },
    { label:'Stress reduction', delta: Math.round(((DEFAULTS.stress - inputs.stress) / 4) * 6) },
  ].filter(i => i.delta !== 0).sort((a,b) => Math.abs(b.delta) - Math.abs(a.delta));

  return (
    <AppShell user={mockUser}>
      <div className="page-enter" style={{ display:'flex', flexDirection:'column', gap:28 }}>
        {/* Header */}
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:12 }}>
          <div>
            <h1 style={{ fontFamily:'Syne,sans-serif', fontSize:26, fontWeight:800,
              color:'#F9FAFB', margin:'0 0 4px' }}>
              Health Trajectory Simulator
            </h1>
            <p style={{ fontSize:14, color:'#6B7280', fontFamily:'DM Sans,sans-serif', margin:0 }}>
              Adjust lifestyle inputs to see how your score could change. All projections are signals, not guarantees.
            </p>
          </div>
          <button className="btn-cyan" style={{ display:'flex', alignItems:'center', gap:6 }}>
            <Share2 size={14} /> Share Plan
          </button>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:24 }} className="sim-grid">
          {/* Sliders */}
          <div className="glass-card" style={{ padding:28, display:'flex', flexDirection:'column', gap:24 }}>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <Sliders size={18} style={{ color:'#00D4FF' }} />
              <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700,
                color:'#F9FAFB', margin:0 }}>Lifestyle Inputs</h2>
            </div>
            <SliderInput label="Daily Steps" min={1000} max={15000} step={500}
              value={inputs.steps} onChange={set('steps')} unit=" steps" icon="🚶"
              description="Target: 8,000+ steps/day" />
            <SliderInput label="Sleep Hours" min={4} max={10} step={0.5}
              value={inputs.sleep} onChange={set('sleep')} unit=" hrs" icon="😴"
              description="Recommended: 7–8 hours" />
            <SliderInput label="Medication Adherence" min={0} max={100} step={5}
              value={inputs.medication} onChange={set('medication')} unit="%" icon="💊"
              description="% of doses taken on time" />
            <SliderInput label="Stress Level" min={1} max={10} step={1}
              value={inputs.stress} onChange={set('stress')} unit="/10" icon="🧘"
              description="Lower is better (1 = relaxed)" />
            <SliderInput label="Diet Quality" min={1} max={10} step={1}
              value={inputs.diet} onChange={set('diet')} unit="/10" icon="🥗"
              description="1 = poor, 10 = excellent" />
          </div>

          {/* Chart + Results */}
          <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
            {/* Score projection */}
            <div className="glass-card" style={{ padding:24 }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
                <h2 style={{ fontFamily:'Syne,sans-serif', fontSize:16, fontWeight:700,
                  color:'#F9FAFB', margin:0 }}>Score Projection</h2>
                <div style={{ display:'flex', gap:4, background:'rgba(255,255,255,0.04)', borderRadius:8, padding:4 }}>
                  {['3m','6m'].map(h => (
                    <button key={h} onClick={() => setHorizon(h)} style={{
                      padding:'5px 14px', borderRadius:6, border:'none', cursor:'pointer',
                      background:horizon===h?'rgba(0,212,255,0.12)':'transparent',
                      color:horizon===h?'#00D4FF':'#9CA3AF',
                      fontFamily:'DM Sans,sans-serif', fontSize:12, transition:'all 0.2s',
                    }}>{h}</button>
                  ))}
                </div>
              </div>

              <div style={{ display:'flex', gap:20, marginBottom:20 }}>
                <div>
                  <p style={{ fontSize:11, color:'#6B7280', margin:'0 0 2px',
                    textTransform:'uppercase', letterSpacing:'0.08em', fontFamily:'DM Sans,sans-serif' }}>
                    Projected Score ({horizon})
                  </p>
                  <p style={{ fontFamily:'Syne,sans-serif', fontSize:38, fontWeight:800,
                    color: gainColor, margin:0 }}>
                    {finalScore}
                    <span style={{ fontSize:14, color:'#9CA3AF', fontWeight:400 }}>/100</span>
                  </p>
                </div>
                <div style={{ borderLeft:'1px solid #1F2937', paddingLeft:20 }}>
                  <p style={{ fontSize:11, color:'#6B7280', margin:'0 0 2px',
                    textTransform:'uppercase', letterSpacing:'0.08em', fontFamily:'DM Sans,sans-serif' }}>
                    Change
                  </p>
                  <p style={{ fontFamily:'Syne,sans-serif', fontSize:38, fontWeight:800,
                    color:gainColor, margin:0 }}>
                    {gain > 0 ? '+' : ''}{gain}
                  </p>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={chartData} margin={{ top:5, right:5, left:-20, bottom:0 }}>
                  <defs>
                    <linearGradient id="projGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#00D4FF" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                  <XAxis dataKey="label" tick={{ fill:'#6B7280', fontSize:11 }} axisLine={false} tickLine={false}/>
                  <YAxis domain={[40,100]} tick={{ fill:'#6B7280', fontSize:11 }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={72} stroke="#374151" strokeDasharray="4 4"/>
                  <Area type="monotone" dataKey="Baseline" stroke="#374151" strokeDasharray="4 4"
                    fill="transparent" name="Baseline" dot={false}/>
                  <Area type="monotone" dataKey="Projected" stroke="#00D4FF" strokeWidth={2.5}
                    fill="url(#projGrad)" name="Projected" dot={{ fill:'#00D4FF', r:4 }}
                    activeDot={{ r:6, fill:'#00D4FF', stroke:'#0A0F1E', strokeWidth:2 }}/>
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Impact breakdown */}
            {impacts.length > 0 && (
              <div className="glass-card" style={{ padding:20 }}>
                <h3 style={{ fontFamily:'Syne,sans-serif', fontSize:14, fontWeight:700,
                  color:'#F9FAFB', margin:'0 0 14px' }}>Key Impact Factors</h3>
                <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
                  {impacts.slice(0,4).map(imp => (
                    <div key={imp.label} style={{ display:'flex', justifyContent:'space-between',
                      alignItems:'center', padding:'8px 12px',
                      background:'rgba(255,255,255,0.03)', borderRadius:8 }}>
                      <span style={{ fontSize:13, color:'#D1D5DB', fontFamily:'DM Sans,sans-serif' }}>
                        {imp.label}
                      </span>
                      <span style={{ fontFamily:'Syne,sans-serif', fontSize:15, fontWeight:700,
                        color: imp.delta > 0 ? '#10B981' : '#EF4444' }}>
                        {imp.delta > 0 ? '+' : ''}{imp.delta} pts
                      </span>
                    </div>
                  ))}
                </div>
                {impacts[0] && (
                  <div style={{ marginTop:12, padding:'10px 14px',
                    background:'rgba(124,58,237,0.08)', borderRadius:10,
                    border:'1px solid rgba(124,58,237,0.2)' }}>
                    <p style={{ fontSize:12, color:'#A78BFA', fontFamily:'DM Sans,sans-serif', margin:0 }}>
                      💡 "{impacts[0].label}" alone saves you {Math.abs(impacts[0].delta)} risk points
                    </p>
                  </div>
                )}
              </div>
            )}

            <div style={{ background:'rgba(0,212,255,0.04)', border:'1px solid rgba(0,212,255,0.12)',
              borderRadius:12, padding:'12px 16px', display:'flex', gap:8, alignItems:'flex-start' }}>
              <Info size={14} style={{ color:'#00D4FF', flexShrink:0, marginTop:2 }} />
              <p style={{ fontSize:12, color:'#9CA3AF', fontFamily:'DM Sans,sans-serif', margin:0, lineHeight:1.6 }}>
                These projections are statistical trends based on population data. They are <strong style={{ color:'#D1D5DB' }}>signals, not diagnoses</strong>. 
                Please consult a healthcare professional before making significant lifestyle changes.
              </p>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width:900px) { .sim-grid { grid-template-columns:1fr !important; } }
      `}</style>
    </AppShell>
  );
}
