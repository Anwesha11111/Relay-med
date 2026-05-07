/**
 * chat.js — AI Chat interface logic with SSE streaming.
 */

let currentSessionId = null;

// ── Session ───────────────────────────────────────────────────────
async function startNewSession() {
  try {
    const { session_id } = await apiNewSession();
    currentSessionId = session_id;
    const container = document.getElementById('chat-messages');
    container.innerHTML = `
      <div class="chat-welcome">
        <div class="welcome-icon">🩺</div>
        <h2>New Session Started</h2>
        <p>Your conversation history has been cleared. How can I help you?</p>
        <div class="quick-prompts">
          <button class="quick-prompt" onclick="sendQuickPrompt('Give me a summary of my current health status.')">Health Summary</button>
          <button class="quick-prompt" onclick="sendQuickPrompt('What do my recent vitals mean?')">Vital Analysis</button>
          <button class="quick-prompt" onclick="sendQuickPrompt('What lifestyle changes would most improve my health?')">Lifestyle Tips</button>
          <button class="quick-prompt" onclick="sendQuickPrompt('Explain my risk findings in simple terms.')">Explain Findings</button>
        </div>
      </div>`;
    showToast('New session started.', 'info', 2000);
  } catch (err) {
    showToast('Failed to start session: ' + err.message, 'error');
  }
}

// ── Send Message ──────────────────────────────────────────────────
async function sendMessage() {
  const inputEl = document.getElementById('chat-input');
  const message = inputEl.value.trim();
  if (!message) return;

  inputEl.value = '';
  inputEl.style.height = 'auto';

  appendMessage('user', message);
  const assistantEl = appendMessage('assistant', '', true); // streaming placeholder

  const sendBtn = document.getElementById('send-btn');
  sendBtn.disabled = true;

  const { session_id } = await apiChatStream({
    session_id: currentSessionId,
    message,
    include_health_context: true,
    onChunk: (chunk) => {
      const bubble = assistantEl.querySelector('.message-bubble');
      if (bubble) {
        bubble.classList.add('streaming-cursor');
        bubble.textContent += chunk;
        scrollChatToBottom();
      }
    },
    onDone: () => {
      const bubble = assistantEl.querySelector('.message-bubble');
      if (bubble) bubble.classList.remove('streaming-cursor');
      sendBtn.disabled = false;
      scrollChatToBottom();
    },
    onError: (err) => {
      const bubble = assistantEl.querySelector('.message-bubble');
      if (bubble) {
        bubble.classList.remove('streaming-cursor');
        bubble.textContent = `Error: ${err.message}`;
        bubble.style.color = 'var(--red)';
      }
      sendBtn.disabled = false;
    },
  });

  if (session_id) currentSessionId = session_id;
}

function sendQuickPrompt(text) {
  const inputEl = document.getElementById('chat-input');
  if (inputEl) inputEl.value = text;
  sendMessage();
}

function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
  // Auto-resize textarea
  const ta = e.target;
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
}

// ── Message Rendering ─────────────────────────────────────────────
function appendMessage(role, text, isStreaming = false) {
  const container = document.getElementById('chat-messages');
  // Remove welcome screen on first real message
  const welcome = container.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const avatarContent = role === 'user' ? '👤' : '🩺';

  const el = document.createElement('div');
  el.className = `message ${role}`;
  el.innerHTML = `
    <div class="message-avatar">${avatarContent}</div>
    <div class="message-content">
      <div class="message-bubble${isStreaming ? ' streaming-cursor' : ''}">${escapeHtml(text)}</div>
      <span class="message-time">${time}</span>
    </div>`;
  container.appendChild(el);
  scrollChatToBottom();
  return el;
}

function scrollChatToBottom() {
  const container = document.getElementById('chat-messages');
  if (container) container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
