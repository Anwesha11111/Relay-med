/**
 * charts.js — Custom SVG chart rendering (no external libraries).
 */

/**
 * Renders an SVG line chart with area fill.
 * @param {string} svgId  - ID of the <svg> element
 * @param {Array}  data   - [{value, label}]
 * @param {object} opts   - { color, unit, yMin, yMax }
 */
function renderLineChart(svgId, data, opts = {}) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  svg.innerHTML = '';

  const W = svg.clientWidth || svg.parentElement.clientWidth || 600;
  const H = parseInt(svg.getAttribute('height')) || 200;
  const PAD = { top: 16, right: 20, bottom: 32, left: 44 };
  const cW = W - PAD.left - PAD.right;
  const cH = H - PAD.top - PAD.bottom;

  if (!data || data.length === 0) return;

  const values = data.map(d => d.value);
  const rawMin = opts.yMin !== undefined ? opts.yMin : Math.min(...values);
  const rawMax = opts.yMax !== undefined ? opts.yMax : Math.max(...values);
  const yMin = rawMin === rawMax ? rawMin - 1 : rawMin;
  const yMax = rawMin === rawMax ? rawMax + 1 : rawMax;
  const yRange = yMax - yMin || 1;

  const xStep = data.length > 1 ? cW / (data.length - 1) : cW;

  // Helpers
  const px = (i) => PAD.left + (data.length > 1 ? i * xStep : cW / 2);
  const py = (v) => PAD.top + cH - ((v - yMin) / yRange) * cH;

  const ns = 'http://www.w3.org/2000/svg';
  const color = opts.color || '#6366f1';

  // Defs (gradient)
  const defs = document.createElementNS(ns, 'defs');
  defs.innerHTML = `
    <linearGradient id="lineGrad-${svgId}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${color}"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
    <linearGradient id="areaGrad-${svgId}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${color}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="${color}" stop-opacity="0.01"/>
    </linearGradient>`;
  svg.appendChild(defs);

  // Grid lines (4 horizontal)
  const gridCount = 4;
  for (let i = 0; i <= gridCount; i++) {
    const y = PAD.top + (cH / gridCount) * i;
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', PAD.left); line.setAttribute('x2', PAD.left + cW);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    line.setAttribute('class', 'chart-grid-line');
    svg.appendChild(line);

    // Y axis labels
    const val = yMax - (yRange / gridCount) * i;
    const text = document.createElementNS(ns, 'text');
    text.setAttribute('x', PAD.left - 6); text.setAttribute('y', y + 4);
    text.setAttribute('text-anchor', 'end'); text.setAttribute('class', 'chart-axis-label');
    text.textContent = Math.round(val * 10) / 10;
    svg.appendChild(text);
  }

  // Build path data
  const points = data.map((d, i) => [px(i), py(d.value)]);
  const pathD = points.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(' ');

  // Area fill
  const areaD = `${pathD} L${points[points.length-1][0]},${PAD.top + cH} L${points[0][0]},${PAD.top + cH} Z`;
  const area = document.createElementNS(ns, 'path');
  area.setAttribute('d', areaD);
  area.setAttribute('fill', `url(#areaGrad-${svgId})`);
  svg.appendChild(area);

  // Line
  const path = document.createElementNS(ns, 'path');
  path.setAttribute('d', pathD);
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke', `url(#lineGrad-${svgId})`);
  path.setAttribute('stroke-width', '2.5');
  path.setAttribute('stroke-linecap', 'round');
  path.setAttribute('stroke-linejoin', 'round');
  svg.appendChild(path);

  // Dots + tooltips
  const tooltipDiv = document.createElement('div');
  tooltipDiv.className = 'chart-tooltip';
  tooltipDiv.style.display = 'none';
  tooltipDiv.style.position = 'fixed';
  svg.parentElement.style.position = 'relative';
  svg.parentElement.appendChild(tooltipDiv);

  points.forEach(([x, y], i) => {
    const circle = document.createElementNS(ns, 'circle');
    circle.setAttribute('cx', x); circle.setAttribute('cy', y);
    circle.setAttribute('r', '4'); circle.setAttribute('class', 'chart-dot');
    circle.style.cursor = 'pointer';
    circle.addEventListener('mouseenter', (e) => {
      const rect = svg.getBoundingClientRect();
      tooltipDiv.style.display = 'block';
      tooltipDiv.style.left = `${x}px`;
      tooltipDiv.style.top  = `${y - 10}px`;
      tooltipDiv.textContent = `${data[i].label ? data[i].label + ': ' : ''}${data[i].value} ${opts.unit || ''}`;
    });
    circle.addEventListener('mouseleave', () => { tooltipDiv.style.display = 'none'; });
    svg.appendChild(circle);

    // X labels (sparse)
    if (data.length <= 10 || i % Math.ceil(data.length / 8) === 0) {
      const text = document.createElementNS(ns, 'text');
      text.setAttribute('x', x); text.setAttribute('y', H - 6);
      text.setAttribute('text-anchor', 'middle'); text.setAttribute('class', 'chart-axis-label');
      text.textContent = data[i].label || '';
      svg.appendChild(text);
    }
  });
}

/**
 * Renders an SVG donut/gauge for trust score.
 * @param {string} svgId
 * @param {number} score  0.0 – 1.0
 */
function renderTrustGauge(svgId, score) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  svg.innerHTML = '';

  const W = 130; const H = 130;
  const cx = W / 2; const cy = H / 2;
  const R = 48; const strokeW = 12;
  const pct = Math.max(0, Math.min(1, score || 0));
  const circumference = 2 * Math.PI * R;
  const dashOffset = circumference * (1 - pct * 0.75);
  const startAngle = 135;
  const ns = 'http://www.w3.org/2000/svg';

  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  const color = pct >= 0.8 ? '#10b981' : pct >= 0.5 ? '#f59e0b' : '#ef4444';

  // Background arc
  const bg = document.createElementNS(ns, 'circle');
  bg.setAttribute('cx', cx); bg.setAttribute('cy', cy); bg.setAttribute('r', R);
  bg.setAttribute('fill', 'none'); bg.setAttribute('stroke', 'rgba(255,255,255,0.06)');
  bg.setAttribute('stroke-width', strokeW);
  bg.setAttribute('stroke-dasharray', `${circumference * 0.75} ${circumference * 0.25}`);
  bg.setAttribute('stroke-linecap', 'round');
  bg.setAttribute('transform', `rotate(${startAngle} ${cx} ${cy})`);
  svg.appendChild(bg);

  // Value arc
  const arc = document.createElementNS(ns, 'circle');
  arc.setAttribute('cx', cx); arc.setAttribute('cy', cy); arc.setAttribute('r', R);
  arc.setAttribute('fill', 'none'); arc.setAttribute('stroke', color);
  arc.setAttribute('stroke-width', strokeW);
  arc.setAttribute('stroke-dasharray', `${circumference * pct * 0.75} ${circumference}`);
  arc.setAttribute('stroke-linecap', 'round');
  arc.setAttribute('transform', `rotate(${startAngle} ${cx} ${cy})`);
  arc.setAttribute('style', `filter: drop-shadow(0 0 6px ${color}80);`);
  svg.appendChild(arc);

  // Center text
  const text = document.createElementNS(ns, 'text');
  text.setAttribute('x', cx); text.setAttribute('y', cy + 6);
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('font-size', '20'); text.setAttribute('font-weight', '700');
  text.setAttribute('font-family', 'Inter, sans-serif');
  text.setAttribute('fill', color);
  text.textContent = score !== null && score !== undefined ? `${Math.round(pct * 100)}%` : '—';
  svg.appendChild(text);

  const sub = document.createElementNS(ns, 'text');
  sub.setAttribute('x', cx); sub.setAttribute('y', cy + 22);
  sub.setAttribute('text-anchor', 'middle');
  sub.setAttribute('font-size', '10'); sub.setAttribute('fill', 'rgba(255,255,255,0.35)');
  sub.setAttribute('font-family', 'Inter, sans-serif');
  sub.textContent = 'trust';
  svg.appendChild(sub);
}
