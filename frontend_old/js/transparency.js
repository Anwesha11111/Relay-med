/**
 * transparency.js — Data Flow Transparency view.
 *
 * Shows:
 *   1. Four-layer pipeline diagram (Ingest → Graph/Predict → Explain → Chat)
 *   2. Per-destination data-flow cards (what goes where, what stays local)
 *   3. Privacy guarantees strip
 *   4. Live audit trace panel (polls /api/v1/audit for real events)
 */

// ── Live Trace ─────────────────────────────────────────────────────────────

let _traceInterval = null;
let _seenAuditIds  = new Set();

function startLiveTrace() {
  stopLiveTrace();
  _pollTrace();                              // immediate first fetch
  _traceInterval = setInterval(_pollTrace, 4000);
}

function stopLiveTrace() {
  if (_traceInterval) { clearInterval(_traceInterval); _traceInterval = null; }
}

async function _pollTrace() {
  try {
    const logs = await apiGetAuditLogs({ hours: 1, limit: 40 });
    if (!logs || logs.length === 0) return;

    const container = document.getElementById('trace-lines');
    if (!container) return;

    // Remove placeholder
    const placeholder = container.querySelector('.trace-empty');
    if (placeholder) placeholder.remove();

    // Add only new entries (avoid duplication across polls)
    const newEntries = logs.filter(e => !_seenAuditIds.has(e.id));
    newEntries.forEach(e => _seenAuditIds.add(e.id));

    if (newEntries.length === 0) return;

    // Prepend newest first
    newEntries.forEach(entry => {
      const line = _buildTraceLine(entry);
      container.insertBefore(line, container.firstChild);
    });

    // Cap at 60 lines
    while (container.children.length > 60) {
      container.removeChild(container.lastChild);
    }
  } catch {
    // Audit endpoint unavailable — silently skip
  }
}

function _buildTraceLine(entry) {
  const div = document.createElement('div');
  div.className = 'trace-line';

  const t   = new Date(entry.timestamp);
  const ts  = `${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}:${String(t.getSeconds()).padStart(2,'0')}`;

  const { layerClass, layerLabel } = _classifyEvent(entry.event_type);
  const isError = entry.event_type.includes('FAIL') || entry.event_type.includes('ERROR') || entry.event_type.includes('DENY');

  div.innerHTML = `
    <span class="trace-time">${ts}</span>
    <span class="trace-layer ${layerClass}">${layerLabel}</span>
    <span class="trace-msg">${_humanise(entry.event_type, entry.payload)}</span>
    <span class="${isError ? 'trace-warn' : 'trace-ok'}">${isError ? '⚠' : '✓'}</span>
  `;
  return div;
}

function _classifyEvent(eventType) {
  if (eventType.includes('INGEST') || eventType.includes('VALID') || eventType.includes('DUPLICATE'))
    return { layerClass: 'layer-ingest', layerLabel: 'INGEST' };
  if (eventType.includes('TRUST'))
    return { layerClass: 'layer-trust', layerLabel: 'TRUST' };
  if (eventType.includes('ENCRYPT') || eventType.includes('DECRYPT'))
    return { layerClass: 'layer-encrypt', layerLabel: 'ENCRYPT' };
  if (eventType.includes('TRIAGE') || eventType.includes('FLAG') || eventType.includes('RULE') || eventType.includes('PREDICT'))
    return { layerClass: 'layer-predict', layerLabel: 'PREDICT' };
  if (eventType.includes('REPORT') || eventType.includes('EXPLAIN') || eventType.includes('SHAP'))
    return { layerClass: 'layer-explain', layerLabel: 'EXPLAIN' };
  if (eventType.includes('CHAT') || eventType.includes('LLM') || eventType.includes('CONVERS'))
    return { layerClass: 'layer-llm', layerLabel: 'LLM' };
  if (eventType.includes('CONSENT'))
    return { layerClass: 'layer-encrypt', layerLabel: 'CONSENT' };
  return { layerClass: 'layer-audit', layerLabel: 'SYSTEM' };
}

function _humanise(eventType, payload) {
  const map = {
    INGEST_SUCCESS:       'Vital record accepted & stored',
    INGEST_DUPLICATE:     'Duplicate record discarded',
    VALIDATION_FAILURE:   'Record failed validation checks',
    CONSENT_GRANT:        `Consent granted for stream "${payload?.stream_id || '—'}"`,
    CONSENT_REVOKE:       `Consent revoked for stream "${payload?.stream_id || '—'}"`,
    TRIAGE_RED_FLAG:      '🔴 Red-flag alert fired — never suppressed',
    TRIAGE_YELLOW_FLAG:   '🟡 Yellow-flag alert raised',
    AUTH_FAILURE:         'Authentication attempt failed',
    SYSTEM_STARTUP:       'Backend started — audit log initialised',
    REPORT_GENERATED:     'Explainability report generated',
    CHAT_REQUEST:         'Chat message routed to local LLM',
  };
  return map[eventType] || eventType.toLowerCase().replace(/_/g, ' ');
}

// ── View Lifecycle ─────────────────────────────────────────────────────────

function showTransparencyView() {
  startLiveTrace();
}

function hideTransparencyView() {
  stopLiveTrace();
}
