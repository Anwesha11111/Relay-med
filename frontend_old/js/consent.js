/**
 * consent.js — Consent manager UI logic.
 */

const STREAMS = [
  { id: 'manual_input',    label: 'Manual Input',    desc: 'Data you type in manually via the Log Vitals form.' },
  { id: 'wearable_vitals', label: 'Wearable Vitals',  desc: 'Automated data from Fitbit, Apple Watch, or similar.' },
  { id: 'ehr_import',      label: 'EHR Import',       desc: 'Records imported from electronic health records systems.' },
];

const USER_ID = 'default';
let consentState = {};  // { stream_id: bool }

async function renderConsentStreams() {
  const container = document.getElementById('consent-streams');
  if (!container) return;

  // Load current consent state
  try {
    const records = await apiGetConsent(USER_ID);
    consentState = {};
    records.forEach(r => { consentState[r.stream_id] = r.consented; });
  } catch {
    consentState = {};
  }

  container.innerHTML = STREAMS.map(stream => {
    const checked = consentState[stream.id] ? 'checked' : '';
    const itemCls = consentState[stream.id] ? 'consented' : '';
    return `
      <div class="consent-stream-item ${itemCls}" id="stream-item-${stream.id}">
        <div class="stream-info">
          <h3>${stream.label}</h3>
          <p>${stream.desc}</p>
        </div>
        <label class="toggle-switch" aria-label="Toggle consent for ${stream.label}">
          <input
            type="checkbox"
            id="consent-toggle-${stream.id}"
            ${checked}
            onchange="toggleConsent('${stream.id}', this.checked)"
          />
          <span class="toggle-slider"></span>
        </label>
      </div>`;
  }).join('');
}

async function toggleConsent(streamId, consented) {
  try {
    await apiSetConsent({ user_id: USER_ID, stream_id: streamId, consented });
    consentState[streamId] = consented;

    const item = document.getElementById(`stream-item-${streamId}`);
    if (item) {
      item.classList.toggle('consented', consented);
    }

    showToast(
      consented
        ? `✅ Consent granted for "${streamId}".`
        : `🔒 Consent revoked for "${streamId}".`,
      consented ? 'success' : 'warning',
      3000,
    );
  } catch (err) {
    showToast('Failed to update consent: ' + err.message, 'error');
    // Revert toggle
    const toggle = document.getElementById(`consent-toggle-${streamId}`);
    if (toggle) toggle.checked = !consented;
  }
}

async function grantAllConsent() {
  for (const stream of STREAMS) {
    await toggleConsent(stream.id, true);
    const toggle = document.getElementById(`consent-toggle-${stream.id}`);
    if (toggle) toggle.checked = true;
  }
  showToast('✅ All consents granted.', 'success');
}

async function revokeAllConsent() {
  for (const stream of STREAMS) {
    await toggleConsent(stream.id, false);
    const toggle = document.getElementById(`consent-toggle-${stream.id}`);
    if (toggle) toggle.checked = false;
  }
  showToast('🔒 All consents revoked.', 'warning');
}
