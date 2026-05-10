/**
 * dashboard.js — Dashboard view logic: KPI cards, charts, findings, ingest form.
 */

// ── View Router ───────────────────────────────────────────────────
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const view = document.getElementById(`view-${name}`);
  const nav  = document.getElementById(`nav-${name}`);
  if (view) view.classList.add('active');
  if (nav)  nav.classList.add('active');
  if (name === 'dashboard')     refreshDashboard();
  if (name === 'audit')         loadAuditLog();
  if (name === 'consent')       renderConsentStreams();
  if (name === 'reports')       loadReports();
  if (name === 'transparency')  showTransparencyView();
  // Stop live trace when leaving the transparency view
  if (name !== 'transparency')  stopLiveTrace();
}

// ── Bootstrap ─────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  await checkSystemHealth();
  await refreshDashboard();
  await renderConsentStreams();
});

async function checkSystemHealth() {
  try {
    const data = await apiHealthCheck();
    const dot  = document.getElementById('system-status');
    const badge = document.getElementById('llm-badge');
    const chatLabel = document.getElementById('chat-llm-label');
    if (dot) dot.innerHTML = '<span class="status-dot"></span><span class="status-text">System Online</span>';
    if (badge) badge.textContent = `LLM: ${(data.llm_provider || '—').toUpperCase()}`;
    if (chatLabel) chatLabel.textContent = (data.llm_provider || '—').toUpperCase();
  } catch {
    const dot = document.getElementById('system-status');
    if (dot) dot.innerHTML = '<span class="status-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444"></span><span class="status-text">Offline</span>';
  }
}

async function refreshDashboard() {
  await Promise.allSettled([
    loadKPIs(),
    loadGraphStats(),
    loadVitalChart('heart_rate'),
    loadReports(),
  ]);
}

// ── KPI Cards ─────────────────────────────────────────────────────
async function loadKPIs() {
  const vitals = ['heart_rate', 'spo2', 'blood_pressure_systolic'];
  const results = await Promise.allSettled(vitals.map(v => apiGetVitalHistory(v, 7)));

  const hrData   = results[0].status === 'fulfilled' ? results[0].value : [];
  const spo2Data = results[1].status === 'fulfilled' ? results[1].value : [];
  const bpData   = results[2].status === 'fulfilled' ? results[2].value : [];

  setKPI('kpi-hr-value',    hrData,   'bpm');
  setKPI('kpi-spo2-value',  spo2Data, '%');
  setKPI('kpi-bp-value',    bpData,   'mmHg');

  // Average trust across all
  const all = [...hrData, ...spo2Data, ...bpData];
  if (all.length) {
    const avg = all.reduce((s, r) => s + (r.trust_score || 0), 0) / all.length;
    const el = document.getElementById('kpi-trust-value');
    if (el) el.innerHTML = `${(avg * 100).toFixed(0)}<span class="kpi-unit">%</span>`;
    renderTrustGauge('trust-gauge', avg);
  }
}

function setKPI(elId, data, unit) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (!data || data.length === 0) { el.innerHTML = `— <span class="kpi-unit">${unit}</span>`; return; }
  const latest = data[data.length - 1];
  el.innerHTML = `${Math.round(latest.value * 10) / 10} <span class="kpi-unit">${unit}</span>`;
}

// ── Chart ─────────────────────────────────────────────────────────
async function loadVitalChart(vitalType) {
  try {
    const data = await apiGetVitalHistory(vitalType, 30);
    const emptyEl = document.getElementById('chart-empty');
    if (!data || data.length === 0) {
      if (emptyEl) emptyEl.classList.remove('hidden');
      return;
    }
    if (emptyEl) emptyEl.classList.add('hidden');

    const chartData = data.map(r => ({
      value: r.value,
      label: new Date(r.timestamp).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
    }));

    const units = {
      heart_rate: 'bpm', spo2: '%', blood_pressure_systolic: 'mmHg',
      blood_pressure_diastolic: 'mmHg', glucose_fasting: 'mg/dL',
      steps: 'steps', sleep_hours: 'hrs',
    };
    renderLineChart('vital-chart', chartData, { unit: units[vitalType] || '' });
  } catch (err) {
    console.warn('Chart load error:', err);
  }
}

// ── Graph Stats ───────────────────────────────────────────────────
async function loadGraphStats() {
  try {
    const stats = await apiGetGraphStats();
    const nodes = document.getElementById('graph-nodes');
    const edges = document.getElementById('graph-edges');
    if (nodes) nodes.textContent = stats.node_count ?? '—';
    if (edges) edges.textContent = stats.edge_count ?? '—';
  } catch {}
}

// ── Risk Findings ─────────────────────────────────────────────────
async function loadReports() {
  try {
    const reports = await apiGetReports();
    renderFindings(reports);
    renderReportCards(reports);
    checkRedFlags(reports);
  } catch (err) {
    console.warn('Reports error:', err);
  }
}

function renderFindings(reports) {
  const container = document.getElementById('findings-list');
  if (!container) return;
  if (!reports || reports.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No active findings. Keep logging data.</p></div>';
    return;
  }
  container.innerHTML = reports.map(r => {
    const sevClass  = r.summary.includes('🔴') ? 'red_flag' : r.summary.includes('🟡') ? 'yellow_flag' : 'info';
    const badgeCls  = sevClass === 'red_flag' ? 'badge-red' : sevClass === 'yellow_flag' ? 'badge-yellow' : 'badge-info';
    const badgeTxt  = sevClass === 'red_flag' ? '🔴 Urgent' : sevClass === 'yellow_flag' ? '🟡 Caution' : 'ℹ️ Info';
    const recs = (r.recommendations || []).map(rec => `<li>${rec}</li>`).join('');
    const warn = r.data_quality_warning ? '<span class="finding-conf">⚠️ Low trust</span>' : '';
    return `
      <div class="finding-card ${sevClass}">
        <div>
          <span class="finding-severity-badge ${badgeCls}">${badgeTxt}</span>
        </div>
        <div class="finding-body">
          <p class="finding-summary">${r.summary}</p>
          ${recs ? `<ul class="finding-recs">${recs}</ul>` : ''}
          <div class="finding-meta">
            <span class="finding-trust">Trust: ${(r.trust_score * 100).toFixed(0)}%</span>
            <span class="finding-conf">Confidence: ${r.confidence_pct}%</span>
            ${warn}
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderReportCards(reports) {
  const container = document.getElementById('reports-container');
  if (!container) return;
  if (!reports || reports.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No findings to report.</p></div>';
    return;
  }
  container.innerHTML = reports.map(r => {
    const recs = (r.recommendations || []).map(rec => `<li>${rec}</li>`).join('');
    const warn = r.data_quality_warning ? `<span class="report-warning">⚠️ Low data quality</span>` : '';
    const cf   = r.counterfactual_summary ? `<p style="margin-top:10px;font-size:13px;color:var(--cyan)">💡 ${r.counterfactual_summary}</p>` : '';
    return `
      <div class="report-card">
        <div class="report-header"><h3>${r.summary.substring(0,80)}…</h3></div>
        <div class="report-body">${r.summary}</div>
        ${cf}
        <div class="report-meta">
          <span class="report-trust">Trust: ${(r.trust_score * 100).toFixed(0)}%</span>
          <span class="report-conf">Confidence: ${r.confidence_pct}%</span>
          ${warn}
          <span style="color:var(--text-dim)">${new Date(r.generated_at).toLocaleString()}</span>
        </div>
        ${recs ? `<div class="report-recs"><h4>Recommendations</h4><ul>${recs}</ul></div>` : ''}
      </div>`;
  }).join('');
}

function checkRedFlags(reports) {
  const banner = document.getElementById('alert-banner');
  if (!banner) return;
  const redFlags = reports.filter(r => r.summary.includes('🔴'));
  if (redFlags.length > 0) {
    banner.classList.remove('hidden');
    banner.innerHTML = `🚨 <strong>${redFlags.length} urgent alert${redFlags.length > 1 ? 's' : ''} detected.</strong> ${redFlags[0].summary.substring(0, 120)}…`;
  } else {
    banner.classList.add('hidden');
  }
}

// ── Ingest Form ───────────────────────────────────────────────────
const VITAL_UNITS = {
  heart_rate: 'bpm', spo2: '%',
  blood_pressure_systolic: 'mmHg', blood_pressure_diastolic: 'mmHg',
  glucose_fasting: 'mg/dL', steps: 'steps',
  sleep_hours: 'hrs', temperature: '°C',
  weight: 'kg', respiratory_rate: 'breaths/min',
  chest_pain_severity: '/10',
};

function updateUnit() {
  const vt = document.getElementById('ingest-vital-type')?.value;
  const unitEl = document.getElementById('ingest-unit');
  if (unitEl && vt) unitEl.value = VITAL_UNITS[vt] || '';
}

async function submitIngest(e) {
  e.preventDefault();
  const btn = document.getElementById('ingest-submit');
  const resultEl = document.getElementById('ingest-result');
  btn.disabled = true; btn.textContent = 'Submitting…';

  const vt   = document.getElementById('ingest-vital-type').value;
  const val  = document.getElementById('ingest-value').value;
  const ts   = document.getElementById('ingest-timestamp').value;
  const src  = document.getElementById('ingest-source').value;
  const stm  = document.getElementById('ingest-stream').value;

  try {
    const result = await apiIngest({
      source: src,
      vital_type: vt,
      value: val,
      unit: VITAL_UNITS[vt] || '',
      timestamp: ts ? new Date(ts).toISOString() : null,
      stream_id: stm,
    });

    let html = `✅ Record accepted. ID: <code>${result.record_id}</code>`;
    if (result.tags?.length)        html += `<br>Tags: ${result.tags.join(', ')}`;
    if (result.triage_alerts?.length) {
      html += `<br><br>🚨 <strong>Triage Alerts:</strong><br>`;
      html += result.triage_alerts.map(a => `• ${a.summary}`).join('<br>');
    }

    const cls = result.triage_alerts?.some(a => a.severity === 'red_flag') ? 'warning' : 'success';
    resultEl.className = `ingest-result ${cls}`;
    resultEl.innerHTML = html;
    resultEl.classList.remove('hidden');
    showToast('Vital logged successfully!', 'success');
    await refreshDashboard();
  } catch (err) {
    resultEl.className = 'ingest-result error';
    resultEl.innerHTML = `❌ ${err.message}`;
    resultEl.classList.remove('hidden');
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Submit Vital';
  }
}

async function quickLog(vitalType, value, unit) {
  try {
    const result = await apiIngest({ source: 'manual', vital_type: vitalType, value, unit, stream_id: 'manual_input' });
    const hasAlert = result.triage_alerts?.some(a => a.severity === 'red_flag');
    showToast(hasAlert ? `⚠️ ALERT: ${result.triage_alerts[0].summary.substring(0,60)}…` : `✅ Logged ${vitalType}: ${value} ${unit}`, hasAlert ? 'warning' : 'success', hasAlert ? 8000 : 3000);
    await refreshDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── Audit Log ─────────────────────────────────────────────────────
async function loadAuditLog() {
  const container = document.getElementById('audit-container');
  const evFilter  = document.getElementById('audit-event-filter')?.value || '';
  const hoursEl   = document.getElementById('audit-hours-filter');
  const hours     = parseInt(hoursEl?.value || '24');

  // Populate event types on first load
  const filterEl = document.getElementById('audit-event-filter');
  if (filterEl && filterEl.options.length === 1) {
    try {
      const types = await apiGetAuditEventTypes();
      types.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t; opt.textContent = t;
        filterEl.appendChild(opt);
      });
    } catch {}
  }

  try {
    const logs = await apiGetAuditLogs({ event_type: evFilter, hours, limit: 200 });
    if (!logs || logs.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No audit entries found for this filter.</p></div>';
      return;
    }
    container.innerHTML = logs.map(e => {
      const cls = getAuditClass(e.event_type);
      const payload = JSON.stringify(e.payload || {}).substring(0, 80);
      return `
        <div class="audit-entry">
          <span class="audit-event-type ${cls}">${e.event_type}</span>
          <span class="audit-timestamp">${new Date(e.timestamp).toLocaleString()}</span>
          <span class="audit-user">${e.user_id}</span>
          <span class="audit-payload">${payload}</span>
        </div>`;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>Error loading audit log: ${err.message}</p></div>`;
  }
}

function getAuditClass(eventType) {
  if (eventType.includes('INGEST') || eventType.includes('DUPLICATE')) return 'audit-type-ingest';
  if (eventType.includes('CONSENT'))   return 'audit-type-consent';
  if (eventType.includes('FLAG') || eventType.includes('TRIAGE') || eventType.includes('ALERT')) return 'audit-type-alert';
  if (eventType.includes('AUTH'))      return 'audit-type-auth';
  if (eventType.includes('SYSTEM') || eventType.includes('STARTUP')) return 'audit-type-system';
  return 'audit-type-default';
}
