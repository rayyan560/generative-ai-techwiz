let ringtoneAudioCtx = null;
let ringtoneOsc1 = null;
let ringtoneOsc2 = null;
let currentCallId = null;
let callTimerInterval = null;

function playRingtoneSound() {
  try {
    if (ringtoneAudioCtx) return;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    ringtoneAudioCtx = new AudioCtx();
    ringtoneOsc1 = ringtoneAudioCtx.createOscillator();
    ringtoneOsc2 = ringtoneAudioCtx.createOscillator();
    const gain = ringtoneAudioCtx.createGain();

    ringtoneOsc1.type = 'sine';
    ringtoneOsc2.type = 'sine';
    ringtoneOsc1.frequency.setValueAtTime(440, ringtoneAudioCtx.currentTime);
    ringtoneOsc2.frequency.setValueAtTime(480, ringtoneAudioCtx.currentTime);

    gain.gain.setValueAtTime(0.12, ringtoneAudioCtx.currentTime);
    ringtoneOsc1.connect(gain);
    ringtoneOsc2.connect(gain);
    gain.connect(ringtoneAudioCtx.destination);

    ringtoneOsc1.start();
    ringtoneOsc2.start();
  } catch (e) {}
}

function stopRingtoneSound() {
  try {
    if (ringtoneOsc1) { ringtoneOsc1.stop(); ringtoneOsc1.disconnect(); ringtoneOsc1 = null; }
    if (ringtoneOsc2) { ringtoneOsc2.stop(); ringtoneOsc2.disconnect(); ringtoneOsc2 = null; }
    if (ringtoneAudioCtx) { ringtoneAudioCtx.close(); ringtoneAudioCtx = null; }
  } catch (e) {}
}

async function toggleStaffPresence() {
  try {
    const r = await fetch('/api/staff/presence/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'} });
    const d = await r.json();
    const isOnline = d.online;
    const btn = document.getElementById('staffPresenceToggleBtn');
    const dot = document.getElementById('staffPresenceDot');
    const txt = document.getElementById('staffPresenceText');
    if (btn && dot && txt) {
      if (isOnline) {
        btn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        btn.style.color = '#059669';
        btn.style.background = 'rgba(16, 185, 129, 0.12)';
        dot.style.background = '#10b981';
        txt.textContent = 'Staff Online';
      } else {
        btn.style.borderColor = 'rgba(244, 63, 94, 0.4)';
        btn.style.color = '#f43f5e';
        btn.style.background = 'rgba(244, 63, 94, 0.12)';
        dot.style.background = '#f43f5e';
        txt.textContent = 'Staff Offline';
      }
    }
  } catch (e) {}
}

async function pollActiveCall() {
  try {
    const r = await fetch('/api/call/status');
    const d = await r.json();
    if (d.active && d.call && d.call.status === 'ringing' && !currentCallId) {
      showIncomingCallModal(d.call);
    } else if ((!d.active || (d.call && (d.call.status === 'ended' || d.call.status === 'declined'))) && currentCallId) {
      closeCallModal();
    }
  } catch (e) {}
}

function showIncomingCallModal(call) {
  currentCallId = call.call_id;
  const nameEl = document.getElementById('snCallName');
  const subEl = document.getElementById('snCallSub');
  const statusEl = document.getElementById('snCallStatusText');
  const arrowsEl = document.getElementById('snCallArrows');
  const modalEl = document.getElementById('snVoiceCallBackdrop');

  if (nameEl) nameEl.textContent = call.client_name || 'Valued Client';
  if (subEl) subEl.textContent = `Client ID: ${call.client_id || 'USR-001'}`;
  if (statusEl) {
    statusEl.textContent = 'INCOMING CALL...';
    statusEl.style.color = '#25d366';
  }
  if (arrowsEl) arrowsEl.style.display = 'flex';
  
  const actionRow = document.getElementById('snCallActionRow');
  if (actionRow) {
    actionRow.innerHTML = `
      <button class="sn-call-btn-circle sn-call-btn-decline" onclick="declineIncomingCall()" title="Decline Call">
        <i class="fa-solid fa-phone-slash"></i>
      </button>
      <button class="sn-call-btn-circle sn-call-btn-accept" id="snCallAcceptBtn" onclick="acceptIncomingCall()" title="Accept Call">
        <i class="fa-solid fa-phone"></i>
      </button>
      <button class="sn-call-btn-circle sn-call-btn-opt" onclick="quickCallMessage()" title="Send Quick Reply">
        <i class="fa-solid fa-comment-dots"></i>
      </button>
    `;
  }

  if (modalEl) modalEl.style.display = 'flex';
  playRingtoneSound();
}

async function acceptIncomingCall() {
  stopRingtoneSound();
  try {
    const response = await fetch('/api/call/accept', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ call_id: currentCallId })
    });
    if (!response.ok) throw new Error('Call request could not be accepted.');
  } catch (e) {
    if (typeof showToast === 'function') showToast(e.message || 'Call request could not be accepted.', 'danger');
    closeCallModal();
    return;
  }

  const statusEl = document.getElementById('snCallStatusText');
  const arrowsEl = document.getElementById('snCallArrows');
  if (statusEl) statusEl.textContent = 'REQUEST ACCEPTED — AUDIO NOT CONNECTED';
  if (arrowsEl) arrowsEl.style.display = 'none';

  let sec = 0;
  if (callTimerInterval) clearInterval(callTimerInterval);
  callTimerInterval = setInterval(() => {
    sec++;
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    if (statusEl) statusEl.textContent = `AUDIO UNAVAILABLE (${m}:${s})`;
  }, 1000);

  const actionRow = document.getElementById('snCallActionRow');
  if (actionRow) {
    actionRow.innerHTML = `
      <button class="sn-call-btn-circle sn-call-btn-decline" onclick="endCurrentCall()" title="End Call">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;
  }
}

async function declineIncomingCall() {
  stopRingtoneSound();
  try {
    await fetch('/api/call/decline', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ call_id: currentCallId })
    });
  } catch (e) {}
  closeCallModal();
}

async function endCurrentCall() {
  stopRingtoneSound();
  if (callTimerInterval) clearInterval(callTimerInterval);
  try {
    await fetch('/api/call/end', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ call_id: currentCallId })
    });
  } catch (e) {}
  closeCallModal();
}

function closeCallModal() {
  stopRingtoneSound();
  if (callTimerInterval) clearInterval(callTimerInterval);
  currentCallId = null;
  const modal = document.getElementById('snVoiceCallBackdrop');
  if (modal) modal.style.display = 'none';
}

function quickCallMessage() {
  if (typeof showToast === 'function') {
    showToast("Quick replies are not connected to the customer chat.", "warning");
  }
  declineIncomingCall();
}

function initLiveHeartbeat() {
  const pill = document.getElementById('liveStreamPill');
  const txt = document.getElementById('liveStatusText');
  if (!pill || !txt) return;

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/triage`;
  
  function connect() {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      pill.style.background = 'rgba(16, 185, 129, 0.16)';
      pill.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      pill.style.color = '#059669';
      txt.textContent = 'Live Feed Active';
    };
    ws.onclose = () => {
      pill.style.background = 'rgba(245, 158, 11, 0.16)';
      pill.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      pill.style.color = '#d97706';
      txt.textContent = 'Reconnecting...';
      setTimeout(connect, 3000);
    };
    ws.onerror = () => {
      ws.close();
    };
  }
  connect();
}

document.addEventListener('DOMContentLoaded', () => {
  setInterval(pollActiveCall, 2500);
  initLiveHeartbeat();
});
