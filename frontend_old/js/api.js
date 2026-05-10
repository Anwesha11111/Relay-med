/**
 * api.js — Centralised API client for the SecureMed backend.
 * All fetch calls go through this module.
 */

const API_BASE = '';  // Same-origin; change to 'http://localhost:9000' for dev

const DEFAULT_USER_ID  = 'default';
const DEFAULT_STREAM_ID = 'manual_input';

// ── Core fetch wrapper ────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Health check ──────────────────────────────────────────────────
async function apiHealthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// ── Ingest ────────────────────────────────────────────────────────
async function apiIngest({ source, vital_type, value, unit, timestamp, stream_id, user_id }) {
  return apiFetch('/ingest', {
    method: 'POST',
    body: JSON.stringify({
      source,
      vital_type,
      value: parseFloat(value),
      unit,
      timestamp: timestamp || new Date().toISOString(),
      stream_id: stream_id || DEFAULT_STREAM_ID,
      user_id:   user_id   || DEFAULT_USER_ID,
    }),
  });
}

// ── Consent ───────────────────────────────────────────────────────
async function apiSetConsent({ user_id, stream_id, consented, version = '1.0' }) {
  return apiFetch('/consent', {
    method: 'POST',
    body: JSON.stringify({ user_id, stream_id, consented, version }),
  });
}

async function apiGetConsent(user_id = DEFAULT_USER_ID) {
  return apiFetch(`/consent/${user_id}`);
}

async function apiCheckConsent(user_id, stream_id) {
  return apiFetch(`/consent/${user_id}/${stream_id}/check`);
}

// ── Reports ───────────────────────────────────────────────────────
async function apiGetReports() {
  return apiFetch('/reports/latest');
}

async function apiGetGraphStats() {
  return apiFetch('/reports/graph/stats');
}

async function apiGetVitalHistory(vital_type, days = 30) {
  return apiFetch(`/reports/vitals/${vital_type}?days=${days}`);
}

// ── Conversation ──────────────────────────────────────────────────
async function apiNewSession() {
  return apiFetch('/conversation/session', { method: 'POST' });
}

async function apiGetHistory(session_id) {
  return apiFetch(`/conversation/history/${session_id}`);
}

/**
 * Stream a chat response using SSE.
 * onChunk(text) called for each token.
 * onDone() called when stream ends.
 * Returns { session_id }.
 */
async function apiChatStream({ session_id, message, include_health_context = true, onChunk, onDone, onError }) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/conversation/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, message, include_health_context, stream: true }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let sid = session_id;
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') { onDone && onDone(); return { session_id: sid }; }
        try {
          const json = JSON.parse(raw);
          if (json.session_id) sid = json.session_id;
          if (json.chunk)      onChunk && onChunk(json.chunk.replace(/\\n/g, '\n').replace(/\\"/g, '"'));
        } catch (_) {}
      }
    }
    onDone && onDone();
    return { session_id: sid };
  } catch (err) {
    onError && onError(err);
    return { session_id };
  }
}

async function apiHealthSummaryStream({ onChunk, onDone, onError }) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/conversation/summary`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') { onDone && onDone(); return; }
        try {
          const json = JSON.parse(raw);
          if (json.chunk) onChunk && onChunk(json.chunk.replace(/\\n/g, '\n').replace(/\\"/g, '"'));
        } catch (_) {}
      }
    }
    onDone && onDone();
  } catch (err) {
    onError && onError(err);
  }
}

// ── Audit ─────────────────────────────────────────────────────────
async function apiGetAuditLogs({ event_type = '', hours = 24, limit = 100 } = {}) {
  const params = new URLSearchParams({ hours, limit });
  if (event_type) params.set('event_type', event_type);
  return apiFetch(`/audit/logs?${params}`);
}

async function apiGetAuditEventTypes() {
  return apiFetch('/audit/event-types');
}

// ── Toast helper ──────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
