// =============================================================
// SupportNova / ResponseX - Ultra High Quality Frontend Engine
// =============================================================

// Global state
let currentComplaints = [];
let selectedComplaintId = null;
let selectedCommComplaintId = null;
let currentCommThreads = [];
let currentRefundRecords = [];
let isOnCall = true;
let soundEnabled = true;
let wsConnection = null;

// -------------------------------------------------------------
// 1. NATIVE WEB AUDIO API SOUND ENGINE (Zero External Assets)
// -------------------------------------------------------------
const SoundFX = {
  ctx: null,
  init() {
    if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
  },
  playClick() {
    if (!soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1200, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.04);
      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.04);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.04);
    } catch (e) {}
  },
  playSuccess() {
    if (!soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, now + i * 0.06);
        gain.gain.setValueAtTime(0.08, now + i * 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.06 + 0.2);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now + i * 0.06);
        osc.stop(now + i * 0.06 + 0.22);
      });
    } catch (e) {}
  },
  playPing() {
    if (!soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.setValueAtTime(1320, now + 0.08);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.36);
    } catch (e) {}
  }
};

function toggleSound() {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById("soundToggleBtn");
  if (btn) {
    btn.innerHTML = soundEnabled ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark" style="color:#e11d48;"></i>';
  }
  showToast(soundEnabled ? "Audio SoundFX Enabled" : "Audio SoundFX Muted", "info");
  if (soundEnabled) SoundFX.playSuccess();
}

// -------------------------------------------------------------
// 2. THEME SWITCHER (Crystal Light vs Obsidian Cyber Glass)
// -------------------------------------------------------------
function initTheme() {
  const saved = localStorage.getItem("supportnova_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  SoundFX.playClick();
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("supportnova_theme", next);
  updateThemeIcon(next);
  showToast(`Theme switched to ${next === 'dark' ? 'Obsidian Cyber Glass' : 'Crystal Light Glass'}`, "info");
}

function updateThemeIcon(theme) {
  const btn = document.getElementById("themeToggleBtn");
  if (btn) {
    btn.innerHTML = theme === "dark" ? '<i class="fa-solid fa-sun" style="color:#f59e0b;"></i>' : '<i class="fa-solid fa-moon"></i>';
  }
}

// -------------------------------------------------------------
// 3. UNIVERSAL COMMAND PALETTE (Cmd + K / Ctrl + K)
// -------------------------------------------------------------
function initCommandPalette() {
  window.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openCommandPalette();
    } else if (e.key === "Escape") {
      closeCommandPalette();
    }
  });
}

function openCommandPalette() {
  SoundFX.playClick();
  const modal = document.getElementById("commandPaletteModal");
  if (!modal) return;
  modal.style.display = "flex";
  const input = document.getElementById("commandInput");
  if (input) {
    input.value = "";
    setTimeout(() => input.focus(), 50);
  }
}

function closeCommandPalette(e) {
  const modal = document.getElementById("commandPaletteModal");
  if (modal) modal.style.display = "none";
}

function handleCommandSearch(query) {
  const q = query.toLowerCase().trim();
  const container = document.getElementById("commandResults");
  if (!container) return;

  if (!q) {
    container.innerHTML = `
      <div class="command-item" onclick="navigateCommand('/admin')">
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-table-cells-large" style="color:var(--cream, #eef0d0);"></i><span>All Complaints Queue (520+ Grievances)</span></div>
        <span style="font-size:0.78rem; color:var(--text-muted);">Jump &rarr;</span>
      </div>
      <div class="command-item" onclick="navigateCommand('/communication')">
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-comments" style="color:var(--cream, #eef0d0);"></i><span>Customer Omnichannel Communication Hub</span></div>
        <span style="font-size:0.78rem; color:var(--text-muted);">Jump &rarr;</span>
      </div>
      <div class="command-item" onclick="navigateCommand('/refunds')">
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-hand-holding-dollar" style="color:#10b981;"></i><span>Refund & Escrow Treasury Ledger</span></div>
        <span style="font-size:0.78rem; color:var(--text-muted);">Jump &rarr;</span>
      </div>
      <div class="command-item" onclick="navigateCommand('/knowledge')">
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-book-bookmark" style="color:#f59e0b;"></i><span>Knowledge Base & Policy Repository</span></div>
        <span style="font-size:0.78rem; color:var(--text-muted);">Jump &rarr;</span>
      </div>
      <div class="command-item" onclick="toggleTheme()">
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-circle-half-stroke" style="color:#c026d3;"></i><span>Toggle Crystal Dark / Light Glass Mode</span></div>
        <span style="font-size:0.78rem; color:var(--text-muted);">Action</span>
      </div>
    `;
    return;
  }

  // Filter complaints & quick actions
  const matched = currentComplaints.filter(c => 
    c.complaint_id.toLowerCase().includes(q) || 
    c.customer_name.toLowerCase().includes(q) || 
    c.complaint_title.toLowerCase().includes(q) ||
    (c.category && c.category.toLowerCase().includes(q))
  ).slice(0, 6);

  if (matched.length === 0) {
    container.innerHTML = `<div style="padding:16px; text-align:center; color:var(--text-muted); font-size:0.9rem;">No matching complaints or commands found.</div>`;
    return;
  }

  container.innerHTML = matched.map(c => `
    <div class="command-item" onclick="closeCommandPalette(); openTriageModal('${c.complaint_id}')">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-family:'JetBrains Mono', monospace; font-weight:700; color:var(--primary);">${c.complaint_id}</span>
        <div>
          <strong style="color:var(--text-heading); font-size:0.9rem;">${c.customer_name}</strong>
          <span style="font-size:0.8rem; color:var(--text-muted); margin-left:8px;">${c.complaint_title.substring(0, 40)}...</span>
        </div>
      </div>
      <span class="badge ${c.urgency === 'Critical' ? 'badge-danger' : 'badge-primary'}">${c.urgency || 'Medium'}</span>
    </div>
  `).join("");
}

function navigateCommand(url) {
  closeCommandPalette();
  window.location.href = url;
}

// -------------------------------------------------------------
// 4. REAL-TIME WEBSOCKET STREAMING & LIVE AGENT PRESENCE
// -------------------------------------------------------------
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/triage`;

  try {
    wsConnection = new WebSocket(wsUrl);

    wsConnection.onopen = () => {
      console.log("Connected to SupportNova Real-Time Triage WebSocket Feed");
      const statusPill = document.getElementById("liveStreamPill");
      if (statusPill) {
        statusPill.style.background = "rgba(16, 185, 129, 0.16)";
        statusPill.style.color = "#059669";
        document.getElementById("liveStatusText").innerText = "Live Stream Active";
      }
    };

    wsConnection.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleWebSocketEvent(msg);
      } catch (e) {
        console.error("Error parsing WS message:", e);
      }
    };

    wsConnection.onclose = () => {
      console.warn("WebSocket disconnected. Retrying in 4s...");
      const statusPill = document.getElementById("liveStreamPill");
      if (statusPill) {
        statusPill.style.background = "rgba(245, 158, 11, 0.16)";
        statusPill.style.color = "#d97706";
        document.getElementById("liveStatusText").innerText = "Reconnecting...";
      }
      setTimeout(initWebSocket, 4000);
    };
  } catch (err) {
    console.error("WebSocket setup failed:", err);
  }
}

function handleWebSocketEvent(msg) {
  if (msg.type === "NEW_COMPLAINT") {
    SoundFX.playPing();
    showToast(`🚨 New Complaint: ${msg.complaint_id} from ${msg.customer_name}`, "warning");
    
    // Prepend to current complaints table if on dashboard
    if (document.getElementById("complaintsTableBody")) {
      const tr = document.createElement("tr");
      tr.style.animation = "slideInRight 0.4s ease-out";
      tr.style.background = "rgba(238, 240, 208, 0.15)";
      tr.onclick = () => openTriageModal(msg.complaint_id);
      
      tr.innerHTML = `
        <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${msg.complaint_id}</td>
        <td>
          <div style="font-weight: 800; color: var(--text-heading);">${msg.customer_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">Standard Tier</div>
        </td>
        <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; color: var(--text-heading);">
          <span style="color:var(--cream, #eef0d0); font-weight:800;">[NEW] </span>${msg.complaint_title}
        </td>
        <td><span class="badge badge-secondary">${msg.category || 'General'}</span></td>
        <td style="font-size: 0.825rem; font-weight: 600;">Customer Care</td>
        <td><span class="badge ${msg.urgency === 'Critical' ? 'badge-danger' : 'badge-primary'}">${msg.urgency || 'Medium'}</span></td>
        <td><strong style="color: var(--text-heading);">${msg.priority || 'P2'}</strong></td>
        <td><span class="badge badge-success">Verified</span></td>
        <td>
          <button class="pill-tab" style="padding: 5px 14px; font-size: 0.78rem;" onclick="event.stopPropagation(); openTriageModal('${msg.complaint_id}')">
            Triage &rarr;
          </button>
        </td>
      `;
      const tbody = document.getElementById("complaintsTableBody");
      tbody.insertBefore(tr, tbody.firstChild);
    }
  } else if (msg.type === "TRIAGE_ACTION_EXECUTED") {
    SoundFX.playSuccess();
    showToast(`✅ Action executed on ${msg.complaint_id} (${msg.action})`, "success");
  }
}

// -------------------------------------------------------------
// 5. TOAST NOTIFICATIONS ENGINE
// -------------------------------------------------------------
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast-alert";

  let icon = "fa-circle-info";
  let iconColor = "var(--cream, #eef0d0)";
  let barColor = "var(--cream, #eef0d0)";
  if (type === "success") { icon = "fa-circle-check"; iconColor = "#10b981"; barColor = "#10b981"; }
  else if (type === "warning") { icon = "fa-triangle-exclamation"; iconColor = "#f59e0b"; barColor = "#f59e0b"; }
  else if (type === "danger" || type === "error") { icon = "fa-circle-exclamation"; iconColor = "#e11d48"; barColor = "#e11d48"; }

  toast.innerHTML = `
    <i class="fa-solid ${icon}" style="font-size: 1.25rem; color: ${iconColor};"></i>
    <div style="flex-grow: 1; font-size: 0.88rem; font-weight: 700; color: var(--text-heading);">${message}</div>
    <button onclick="this.parentElement.remove()" style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:1.1rem; opacity:0.7;">&times;</button>
    <div class="toast-progress-bar" style="background: ${barColor};"></div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(60px) scale(0.95)";
    setTimeout(() => toast.remove(), 250);
  }, 4500);
}

// -------------------------------------------------------------
// 6. 3D CARD TILT MICRO-INTERACTIONS
// -------------------------------------------------------------
function init3DCardTilt() {
  const cards = document.querySelectorAll(".summary-card, .glass-card, .customer-hero-card, .pipeline-card");
  cards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -5;
      const rotateY = ((x - centerX) / centerX) * 5;
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
    });
  });
}

// -------------------------------------------------------------
// 7. INITIALIZATION & ROUTING
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initCommandPalette();
  initWebSocket();

  // Route / Page detectors
  if (document.getElementById("complaintsTableBody")) {
    loadComplaints();
  }
  if (document.getElementById("commThreadsList")) {
    loadCommunicationThreads();
  }
  if (document.getElementById("refundsTableBody")) {
    loadRefundsDashboard();
  }
  if (document.getElementById("knowledgeTableBody")) {
    loadKnowledgeList();
  }
  if (document.getElementById("rulesTableBody")) {
    loadRulesList();
  }
  if (document.getElementById("categoryChart")) {
    loadAnalyticsDashboard();
  }

  // Setup 3D tilt after content renders
  setTimeout(init3DCardTilt, 500);

  // Global search input listener
  const searchInput = document.getElementById("globalSearchInput");
  if (searchInput) {
    searchInput.addEventListener("keyup", (e) => {
      const q = e.target.value.toLowerCase();
      const rows = document.querySelectorAll("#complaintsTableBody tr, #knowledgeTableBody tr, #rulesTableBody tr, #refundsTableBody tr");
      rows.forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
      });
    });
  }
});

// Telephony Call Simulation
function toggleCallSimulation() {
  SoundFX.playClick();
  isOnCall = !isOnCall;
  const btn = document.getElementById("callSimBtn");
  const text = document.getElementById("callBtnText");
  const commBtnText = document.getElementById("commCallBtnText");
  const telephonyBadge = document.getElementById("telephonyLiveBadge");

  if (isOnCall) {
    if (btn) btn.style.background = "var(--success-gradient)";
    if (text) text.innerText = "On Call";
    if (commBtnText) commBtnText.innerText = "On Call Simulation";
    if (telephonyBadge) {
      telephonyBadge.className = "badge badge-success";
      telephonyBadge.innerHTML = '<i class="fa-solid fa-circle" style="font-size: 0.5rem;"></i> Active Call';
    }
    showToast("Telephony Simulation: Live Audio Channel Connected", "success");
  } else {
    if (btn) btn.style.background = "#64748b";
    if (text) text.innerText = "Call Ended";
    if (commBtnText) commBtnText.innerText = "Call Ended (Resume)";
    if (telephonyBadge) {
      telephonyBadge.className = "badge badge-secondary";
      telephonyBadge.innerHTML = '<i class="fa-solid fa-phone-slash" style="font-size: 0.5rem;"></i> Call Disconnected';
    }
    showToast("Telephony Simulation: Call Ended", "warning");
  }
}

// -------------------------------------------------------------
// 8. ALL COMPLAINTS & DASHBOARD TRIAGE
// -------------------------------------------------------------
async function loadComplaints() {
  try {
    const res = await fetch("/api/complaints?limit=100");
    const data = await res.json();
    currentComplaints = data.complaints;
    renderComplaintsTable(currentComplaints);
    
    if (currentComplaints.length > 0) {
      updateHeroCustomerCard(currentComplaints[0]);
    }
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading complaints:", e);
  }
}

function updateHeroCustomerCard(c) {
  const nameEl = document.getElementById("heroCustomerName");
  if (!nameEl) return;
  nameEl.innerText = c.customer_name || "Customer";
  document.getElementById("heroCustomerEmail").innerText = c.customer_email || "N/A";
  document.getElementById("heroCustomerPhone").innerText = c.customer_phone || "+1 98567 45956";
  document.getElementById("heroComplaintId").innerText = c.complaint_id;
  document.getElementById("heroCategory").innerText = c.category || "General";
  
  const priBadge = document.getElementById("heroPriorityBadge");
  priBadge.innerText = (c.priority || "P2") + " - " + (c.urgency || "Medium");
  priBadge.className = `badge ${c.urgency === 'Critical' ? 'badge-danger' : (c.urgency === 'High' ? 'badge-warning' : 'badge-primary')}`;
}

function renderComplaintsTable(list) {
  const tbody = document.getElementById("complaintsTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 28px; color: var(--text-muted);">No complaints found in current view.</td></tr>`;
    return;
  }

  list.forEach(c => {
    const tr = document.createElement("tr");
    tr.onclick = () => {
      updateHeroCustomerCard(c);
      openTriageModal(c.complaint_id);
    };

    const compStatus = c.comparison ? c.comparison.verification_status : "Verified";
    const compClass = compStatus === "Verified" ? "badge-success" : (compStatus.includes("Warning") ? "badge-warning" : "badge-danger");

    tr.innerHTML = `
      <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${c.complaint_id}</td>
      <td>
        <div style="font-weight: 800; color: var(--text-heading);">${c.customer_name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">${c.customer_type || 'Standard'} Tier</div>
      </td>
      <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; color: var(--text-heading);">
        ${c.is_adversarial ? '<span style="color:#e11d48; font-weight:800;">🛡️ [Adversarial] </span>' : ''}
        ${c.is_duplicate ? '<span style="color:#d97706; font-weight:800;">🔁 [Repeat] </span>' : ''}
        ${c.complaint_title}
      </td>
      <td><span class="badge badge-secondary">${c.category || 'General'}</span></td>
      <td style="font-size: 0.825rem; font-weight: 600;">${c.department || 'Customer Care'}</td>
      <td><span class="badge ${c.urgency === 'Critical' ? 'badge-danger' : (c.urgency === 'High' ? 'badge-warning' : 'badge-primary')}">${c.urgency || 'Medium'}</span></td>
      <td><strong style="color: var(--text-heading);">${c.priority || 'P2'}</strong></td>
      <td><span class="badge ${compClass}">${compStatus}</span></td>
      <td>
        <button class="pill-tab" style="padding: 5px 14px; font-size: 0.78rem;" onclick="event.stopPropagation(); openTriageModal('${c.complaint_id}')">
          Triage &rarr;
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterByTab(tab) {
  SoundFX.playClick();
  document.querySelectorAll(".tab-pills-row .pill-tab").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }

  if (tab === "All") {
    renderComplaintsTable(currentComplaints);
  } else if (tab === "Critical") {
    renderComplaintsTable(currentComplaints.filter(c => c.urgency === "Critical" || c.priority === "P0"));
  } else if (tab === "Refund") {
    renderComplaintsTable(currentComplaints.filter(c => c.category === "Refund Request" || c.category === "Billing & Charges"));
  } else if (tab === "Adversarial") {
    renderComplaintsTable(currentComplaints.filter(c => c.is_adversarial || (c.comparison && c.comparison.prompt_injection_detected)));
  } else if (tab === "ManualReview") {
    renderComplaintsTable(currentComplaints.filter(c => c.status === "Manual Review Required" || (c.comparison && c.comparison.requires_manual_review)));
  } else if (tab === "Resolved") {
    renderComplaintsTable(currentComplaints.filter(c => c.status === "Resolved" || c.status === "Closed"));
  }
}

async function openTriageModal(complaintId) {
  SoundFX.playClick();
  selectedComplaintId = complaintId;
  const modal = document.getElementById("triageModal");
  if (!modal) return;
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/complaints/${complaintId}`);
    const data = await res.json();

    document.getElementById("modalComplaintTitle").innerText = data.complaint_title;
    document.getElementById("modalComplaintSubtitle").innerText = `ID: ${data.complaint_id} | Customer: ${data.customer_name} (${data.customer_type}) | Product: ${data.product_or_service || 'N/A'}`;
    document.getElementById("modalRawDescription").innerText = data.complaint_description;

    // 🧠 Customer Emotion & Frustration Heatmap Rendering
    const sent = data.sentiment_telemetry || {};
    const frScore = sent.frustration_score || 55;
    const emState = sent.emotion_state || "Frustrated & Dissatisfied";
    const triggers = sent.key_emotional_triggers || ["general grievance"];

    const emCard = document.getElementById("modalEmotionCard");
    const emStateEl = document.getElementById("modalEmotionState");
    const frScoreEl = document.getElementById("modalFrustrationScore");
    const frBarEl = document.getElementById("modalFrustrationBar");
    const trChipsEl = document.getElementById("modalTriggerChips");

    if (emStateEl) emStateEl.innerText = emState;
    if (frScoreEl) frScoreEl.innerText = `${frScore}% / 100`;
    if (frBarEl) {
      frBarEl.style.width = `${frScore}%`;
      frBarEl.style.background = frScore > 70 ? 'linear-gradient(90deg, #f59e0b, #e11d48)' : 'linear-gradient(90deg, #10b981, #f59e0b)';
    }
    if (trChipsEl) {
      trChipsEl.innerHTML = triggers.map(t => `<span class="trigger-chip"><i class="fa-solid fa-fire"></i> ${t}</span>`).join("");
    }

    // Adversarial Banner
    const advBanner = document.getElementById("modalAdversarialBanner");
    if (data.genai_analysis && data.genai_analysis.adversarial_warning) {
      advBanner.style.display = "block";
      advBanner.innerText = `🛡️ SECURITY WARNING: ${data.genai_analysis.adversarial_warning}`;
    } else {
      advBanner.style.display = "none";
    }

    // Comparison summary
    const comp = data.comparison || {};
    const vBadge = document.getElementById("modalVerificationStatus");
    vBadge.innerText = comp.verification_status || "Verified";
    vBadge.className = `badge ${comp.verification_status === 'Verified' ? 'badge-success' : (comp.verification_status.includes('Warning') ? 'badge-warning' : 'badge-danger')}`;
    
    document.getElementById("modalCoverageScore").innerText = `${comp.mandatory_coverage_score || 100}%`;
    document.getElementById("modalTraceabilityScore").innerText = `${comp.source_traceability_score || 100}%`;
    document.getElementById("modalConsistencyScore").innerText = `${comp.consistency_score || 100}%`;

    // Pipeline 1: GenAI
    const ai = data.genai_analysis || {};
    document.getElementById("genaiCategory").innerText = ai.category || "-";
    document.getElementById("genaiSubcategory").innerText = ai.subcategory || "-";
    document.getElementById("genaiDept").innerText = ai.recommended_department || "-";
    document.getElementById("genaiUrgency").innerText = ai.urgency || "-";
    document.getElementById("genaiPriority").innerText = ai.priority || "-";
    document.getElementById("genaiPolicy").innerText = ai.referenced_policy_id || "POL-CMP-01";
    document.getElementById("genaiEscalation").innerText = ai.escalation_required ? `Yes (${ai.escalation_tier})` : "No";

    const stepsUl = document.getElementById("genaiStepsList");
    stepsUl.innerHTML = (ai.resolution_steps || []).map(s => `<li>${s}</li>`).join("");
    document.getElementById("genaiCustomerResponse").value = ai.customer_response || "";

    // Pipeline 2: Ground Truth
    const gt = data.ground_truth || {};
    document.getElementById("gtRuleId").innerText = gt.rule_id_matched || "RUL-GEN-001";
    document.getElementById("gtDept").innerText = gt.expected_department || "-";
    document.getElementById("gtEscalation").innerText = gt.mandatory_escalation ? "YES (MANDATORY)" : "No";
    document.getElementById("gtTier").innerText = gt.escalation_tier || "Tier 1";
    document.getElementById("gtPolicy").innerText = `${gt.applicable_policy_id || 'POL-GEN-01'} (${gt.policy_status || 'Active'})`;
    document.getElementById("gtRefund").innerText = gt.refund_eligible ? "ELIGIBLE" : "NOT ELIGIBLE";

    const gtStepsUl = document.getElementById("gtMandatoryStepsList");
    gtStepsUl.innerHTML = (gt.mandatory_resolution_steps || []).map(s => `<li>${s}</li>`).join("");

    const probDiv = document.getElementById("gtProhibitedActions");
    if (comp.unauthorized_promise_detected) {
      probDiv.innerHTML = `<strong>VIOLATION:</strong> ${(comp.unsupported_claims_flagged || []).join("; ")}`;
    } else {
      probDiv.innerText = "Zero policy violations detected in GenAI response.";
    }

    const clarBox = document.getElementById("clarificationQuestionsBox");
    if (clarBox) {
      if (!data.order_id || !data.product_or_service || data.complaint_description.length < 40) {
        clarBox.innerHTML = `
          <ul style="padding-left: 18px; margin: 0;">
            ${!data.order_id ? '<li>Could you please provide your official NovaTech 10-digit Order ID or Invoice number?</li>' : ''}
            ${!data.product_or_service ? '<li>Could you confirm the exact hardware model and serial number from the back label?</li>' : ''}
            <li>Could you describe when the defect first occurred and attach a clear photo of the hardware?</li>
          </ul>
        `;
      } else {
        clarBox.innerHTML = `<span style="color: #059669; font-weight: 700;"><i class="fa-solid fa-circle-check"></i> All primary entity specifications verified. No clarification required.</span>`;
      }
    }

  } catch (e) {
    console.error(e);
  }
}

function insertClarificationQuestions() {
  const respEl = document.getElementById("genaiCustomerResponse");
  const questions = "\n\nTo help us expedite your request, could you please confirm:\n1. Your official NovaTech Order/Invoice number?\n2. The exact hardware serial number?\n3. A clear photo showing the reported defect?";
  if (respEl) {
    respEl.value += questions;
    showToast("Clarification questions appended to response", "info");
  }
}

function changeResponseTone(tone) {
  const respEl = document.getElementById("genaiCustomerResponse");
  if (!respEl) return;
  const current = respEl.value;
  if (tone === "Empathetic") {
    respEl.value = `Dear Customer,\n\nWe are sincerely sorry to hear about your experience with our product. We completely understand how frustrating this disruption is to your daily workflow, and our dedicated engineering team is prioritizing your case immediately.\n\n${current.replace(/^Dear.*?\n\n/i, '')}`;
  } else if (tone === "Concise") {
    respEl.value = `Hello,\n\nYour complaint has been logged and assigned under reference. We have reviewed the applicable warranty policy and initiated immediate diagnostics.\n\nNext steps: Verification in progress within standard SLA.`;
  } else if (tone === "Formal") {
    respEl.value = `Official Communication - NovaTech Global Support Operations\n\nThis notice confirms receipt of your formal grievance. The matter has been recorded and submitted for policy compliance review pursuant to Standard Operating Procedure terms.`;
  } else {
    respEl.value = current;
  }
  showToast(`Response draft updated to ${tone} tone`, "info");
}

function generateFollowUpTemplate(type) {
  const respEl = document.getElementById("genaiCustomerResponse");
  if (!respEl) return;
  
  if (type === "request_info") {
    respEl.value = `Dear Customer,\n\nThank you for reaching out to NovaTech Support. To ensure we apply the correct warranty coverage, please reply with a clear photograph or video showing the reported issue along with your original purchase receipt.\n\nBest regards,\nNovaTech Resolution Team`;
  } else if (type === "resolution_confirm") {
    respEl.value = `Dear Customer,\n\nWe are pleased to inform you that your case has been fully reviewed and approved for resolution under our active warranty terms. Your replacement hardware unit is scheduled for immediate shipment.\n\nTracking details will follow shortly.`;
  } else if (type === "refund_update") {
    respEl.value = `Dear Customer,\n\nYour refund authorization has been approved by our financial audit department. The credited amount will reflect in your original payment method within 3-5 business days.\n\nThank you for your patience.`;
  } else if (type === "replacement_eta") {
    respEl.value = `Dear Customer,\n\nYour replacement order has been processed with priority expedited shipping. Estimated delivery: 2 business days via FedEx Priority.\n\nCarrier Tracking Ref: FDX-${Math.floor(10000000 + Math.random() * 90000000)}`;
  } else if (type === "case_closure") {
    respEl.value = `Dear Customer,\n\nYour ticket has been marked as Resolved. If you have any further questions or if the issue reoccurs, please let us know. We would appreciate your feedback on our service.\n\nThank you for choosing NovaTech.`;
  }
  showToast("Follow-up template inserted", "success");
}

async function reassignSelectedDepartment() {
  const sel = document.getElementById("reassignDeptSelect");
  const dept = sel ? sel.value : "";
  if (!dept) {
    showToast("Please select a department to reassign.", "warning");
    return;
  }
  const targetId = selectedComplaintId || selectedCommComplaintId;
  if (!targetId) {
    showToast("Please select an active complaint first.", "warning");
    return;
  }

  const formData = new FormData();
  formData.append("action", "reassign");
  formData.append("new_department", dept);
  formData.append("reviewer_notes", `Reassigned to ${dept} by Support Agent`);

  try {
    const res = await fetch(`/api/complaints/${targetId}/triage`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      showToast(`Complaint ${targetId} reassigned to ${dept}!`, "success");
      closeTriageModal();
      loadComplaints();
    }
  } catch (e) {
    showToast("Error reassigning department: " + e, "danger");
  }
}

function closeTriageModal() {
  SoundFX.playClick();
  const modal = document.getElementById("triageModal");
  if (modal) modal.style.display = "none";
}

async function executeTriageAction(action) {
  SoundFX.playClick();
  const targetId = selectedComplaintId || selectedCommComplaintId;
  if (!targetId) {
    showToast("Please select an active complaint first.", "warning");
    return;
  }
  const noteInput = document.getElementById("reviewerNoteInput");
  const note = noteInput ? noteInput.value : "Action triggered by agent";
  const escTierSel = document.getElementById("escalateTierSelect");
  const escTier = escTierSel ? escTierSel.value : "Tier 1";

  const formData = new FormData();
  formData.append("action", action);
  formData.append("reviewer_notes", action === "escalate" ? `${note} [Escalated to ${escTier}]` : note);

  try {
    const res = await fetch(`/api/complaints/${targetId}/triage`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      showToast(`Action '${action}' applied to ${targetId}!`, "success");
      closeTriageModal();
      if (document.getElementById("complaintsTableBody")) loadComplaints();
      if (document.getElementById("commThreadsList")) loadCommunicationThreads();
    }
  } catch (e) {
    showToast("Error executing triage action: " + e, "danger");
  }
}

// -------------------------------------------------------------
// 9. KNOWLEDGE BASE & POLICY INSPECTION
// -------------------------------------------------------------
async function loadKnowledgeList() {
  try {
    const res = await fetch("/api/knowledge/list");
    const data = await res.json();
    const tbody = document.getElementById("knowledgeTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const docs = data.documents || [];
    if (docs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:var(--text-muted);">No knowledge documents indexed.</td></tr>`;
      return;
    }

    docs.forEach(doc => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${doc.document_id}</td>
        <td><strong style="color: var(--text-heading);">${doc.title}</strong></td>
        <td>${doc.doc_type || 'Active Policy'}</td>
        <td><span class="badge badge-primary">${doc.category || 'General'}</span></td>
        <td>${doc.version || 'v2.0'}</td>
        <td><strong>${doc.total_chunks || 4} Chunks</strong></td>
        <td><span class="badge badge-success">${doc.status || 'Active'}</span></td>
        <td>
          <button class="pill-tab" style="padding: 5px 14px; font-size: 0.78rem;" onclick="inspectPolicy('${doc.document_id}')">
            Inspect &rarr;
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading knowledge docs:", e);
  }
}

async function inspectPolicy(docId) {
  SoundFX.playClick();
  const modal = document.getElementById("policyInspectModal") || document.getElementById("policyModal");
  if (!modal) return;
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/knowledge/document/${docId}`);
    const data = await res.json();

    // Support both ID naming schemes
    const titleEl = document.getElementById("inspectDocTitle") || document.getElementById("modalPolicyTitle");
    if (titleEl) titleEl.innerText = data.title || docId;

    const subEl = document.getElementById("inspectDocSubtitle") || document.getElementById("modalPolicyDocId");
    if (subEl) subEl.innerText = `Document ID: ${data.document_id} | Version: ${data.version || 'v2.0'}`;

    const catEl = document.getElementById("inspectDocCategory") || document.getElementById("modalPolicyCategory");
    if (catEl) catEl.innerText = data.category || "General";

    const countEl = document.getElementById("inspectDocChunkCount") || document.getElementById("modalPolicyChunksCount");
    if (countEl) countEl.innerText = `${(data.chunks || []).length} Traceable Chunks`;

    const chunksCont = document.getElementById("inspectChunksList") || document.getElementById("modalPolicyChunks");
    if (chunksCont) {
      chunksCont.innerHTML = (data.chunks || []).map((c, i) => `
        <div style="background: var(--glass-bg-subtle); border: 1px solid var(--glass-border); border-radius: var(--radius-sm); padding: 18px; margin-bottom: 14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="font-family:'JetBrains Mono', monospace; color:var(--primary); font-size:0.85rem;">Chunk #${i+1}: ${c.chunk_id || 'CHK-'+(i+1)}</strong>
            <span class="badge badge-primary" style="font-size:0.75rem;">Clause Section ${c.section_number || (i+1)}</span>
          </div>
          <p style="font-size:0.92rem; color:var(--text-body); line-height:1.6; white-space:pre-wrap;">${c.text_content || c.clause_text}</p>
        </div>
      `).join("");
    }
  } catch (e) {
    console.error("Error inspecting policy:", e);
  }
}

function closePolicyInspectModal() {
  SoundFX.playClick();
  const modal = document.getElementById("policyInspectModal") || document.getElementById("policyModal");
  if (modal) modal.style.display = "none";
}

function closePolicyModal() {
  closePolicyInspectModal();
}

// 🔍 RAG Policy Drift & Rule Contradiction Auditor
async function openPolicyConflictModal() {
  SoundFX.playClick();
  const modal = document.getElementById("policyConflictModal");
  if (!modal) return;
  modal.style.display = "flex";

  const cont = document.getElementById("policyConflictsList");
  if (!cont) return;
  cont.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.95rem;"><i class="fa-solid fa-spinner fa-spin"></i> Scanning cross-clause RAG contradictions against 105+ Ground-Truth rules...</div>`;

  try {
    const res = await fetch("/api/knowledge/conflicts");
    const data = await res.json();
    const conflicts = data.conflicts || [];

    if (conflicts.length === 0) {
      cont.innerHTML = `<div style="text-align:center; padding:30px; color:#10b981; font-weight:700;">Zero policy drift detected. All rules 100% compliant.</div>`;
      return;
    }

    cont.innerHTML = conflicts.map(c => `
      <div style="background: var(--glass-bg-subtle); border: 1px solid var(--glass-border); border-left: 4px solid ${c.severity === 'HIGH' ? '#e11d48' : '#f59e0b'}; border-radius: var(--radius-sm); padding: 18px 22px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <div>
            <strong style="font-family:'JetBrains Mono', monospace; color:var(--primary); font-size:0.9rem;">${c.conflict_id}</strong>
            <span style="font-weight:700; color:var(--text-heading); margin-left:10px;">${c.category} &bull; ${c.topic}</span>
          </div>
          <span class="badge ${c.severity === 'HIGH' ? 'badge-danger' : 'badge-warning'}">${c.severity} RISK</span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin: 10px 0; font-size:0.86rem;">
          <div style="background: rgba(255,255,255,0.4); padding:10px; border-radius:8px; border:1px solid var(--glass-border);">
            <strong style="color:var(--text-heading); font-size:0.8rem;">Clause A (${c.clause_a_ref})</strong>
            <div style="color:var(--text-body); margin-top:4px;">"${c.clause_a_text}"</div>
          </div>
          <div style="background: rgba(255,255,255,0.4); padding:10px; border-radius:8px; border:1px solid var(--glass-border);">
            <strong style="color:var(--text-heading); font-size:0.8rem;">Clause B (${c.clause_b_ref})</strong>
            <div style="color:var(--text-body); margin-top:4px;">"${c.clause_b_text}"</div>
          </div>
        </div>
        <div style="font-size:0.82rem; color:#047857; background: rgba(16, 185, 129, 0.1); padding:8px 12px; border-radius:6px; margin-top:6px;">
          <strong>🛡️ System Precedence Resolution:</strong> ${c.resolution_guideline} (Precedence Winner: <strong>${c.precedence_winner}</strong>)
        </div>
      </div>
    `).join("");
  } catch (e) {
    cont.innerHTML = `<div style="color:#e11d48; text-align:center; padding:20px;">Error scanning policies: ${e}</div>`;
  }
}

function filterPolicyTable() {
  const input = document.getElementById("policyFilterInput");
  if (!input) return;
  const q = input.value.toLowerCase();
  const rows = document.querySelectorAll("#knowledgeTableBody tr");
  rows.forEach(r => {
    r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
  });
}

async function handlePolicyUpload(e) {
  e.preventDefault();
  SoundFX.playClick();
  const form = e.target;
  const formData = new FormData(form);

  try {
    showToast("Parsing and indexing policy chunks via PyMuPDF...", "info");
    const res = await fetch("/api/knowledge/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      showToast(`Document indexed successfully! ${data.chunks_count || 4} chunks generated.`, "success");
      document.getElementById("uploadPolicyModal").style.display = "none";
      form.reset();
      loadKnowledgeList();
    }
  } catch (err) {
    showToast("Error uploading policy: " + err, "danger");
  }
}

// -------------------------------------------------------------
// 10. RULES MATRIX (105+ DETERMINISTIC RULES)
// -------------------------------------------------------------
async function loadRulesList() {
  try {
    const res = await fetch("/api/rules/list");
    const data = await res.json();
    const tbody = document.getElementById("rulesTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const rules = data.rules || [];
    const countBadge = document.getElementById("rulesCountBadge");
    if (countBadge) countBadge.textContent = `${rules.length} Rules Active`;

    if (rules.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: var(--text-muted);">No rules active.</td></tr>`;
      return;
    }

    rules.forEach(r => {
      const polId = r.policy_id || r.applicable_policy_id || "POL-GEN-01";
      const compMax = (r.max_compensation_usd !== undefined && r.max_compensation_usd !== null) 
        ? `$${r.max_compensation_usd}` 
        : (r.compensation_max || "$150.00");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: #059669;">${r.rule_id || 'R-000'}</td>
        <td><strong style="color: var(--text-heading);">${r.category || 'General'}</strong></td>
        <td>${r.subcategory || 'Standard'}</td>
        <td><span class="badge badge-primary">${r.department || 'Triage'}</span></td>
        <td><span class="badge ${r.urgency === 'Critical' ? 'badge-danger' : 'badge-warning'}">${r.urgency || 'Medium'}</span></td>
        <td><span style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; font-weight:700; color:var(--primary);">${polId}</span></td>
        <td>${r.mandatory_escalation ? '<span class="badge badge-danger">MANDATORY</span>' : '<span class="badge badge-secondary">No</span>'}</td>
        <td>${r.refund_eligible ? '<span class="badge badge-success">Eligible</span>' : '<span class="badge badge-secondary">No</span>'}</td>
        <td style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#10b981;">${compMax}</td>
      `;
      tbody.appendChild(tr);
    });
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading rules matrix:", e);
    const tbody = document.getElementById("rulesTableBody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 24px; color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Error loading rules matrix feed.</td></tr>`;
    }
  }
}

// -------------------------------------------------------------
// 11. COMMUNICATION HUB
// -------------------------------------------------------------
async function loadCommunicationThreads() {
  try {
    const res = await fetch("/api/communication/threads");
    const data = await res.json();
    currentCommThreads = data.threads || [];
    renderCommunicationThreads(currentCommThreads);

    if (currentCommThreads.length > 0) {
      selectCommunicationThread(currentCommThreads[0].complaint_id);
    }
  } catch (e) {
    console.error("Error loading comm threads:", e);
  }
}

function renderCommunicationThreads(threads) {
  const cont = document.getElementById("commThreadsList");
  if (!cont) return;
  cont.innerHTML = "";

  threads.forEach(t => {
    const div = document.createElement("div");
    div.className = `comm-thread-item ${t.complaint_id === selectedCommComplaintId ? 'active' : ''}`;
    div.onclick = () => selectCommunicationThread(t.complaint_id);

    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-weight: 800; font-size: 0.92rem; color: var(--text-heading);">${t.customer_name}</span>
        <span style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${t.complaint_id}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--primary); font-weight: 700; margin-bottom: 4px;">${t.complaint_title}</div>
      <div style="font-size: 0.78rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${t.last_message}</div>
    `;
    cont.appendChild(div);
  });
}

async function selectCommunicationThread(cid) {
  SoundFX.playClick();
  selectedCommComplaintId = cid;
  renderCommunicationThreads(currentCommThreads);

  try {
    const res = await fetch(`/api/communication/thread/${cid}`);
    const data = await res.json();

    document.getElementById("commCustomerHeaderName").innerText = data.customer_name || "Customer";
    document.getElementById("commComplaintRefCode").innerText = data.complaint_id;
    document.getElementById("commCustomerEmail").innerText = data.customer_email || "N/A";
    document.getElementById("commCustomerPhone").innerText = data.customer_phone || "N/A";
    document.getElementById("commCustomerTier").innerText = data.customer_type || "Standard";

    // Messages
    const stream = document.getElementById("commMessagesStream");
    stream.innerHTML = (data.messages || []).map(m => `
      <div class="chat-bubble ${m.sender === 'agent' ? 'agent' : 'customer'}">
        <div style="font-weight: 700; font-size: 0.76rem; margin-bottom: 3px;">${m.sender_name || (m.sender === 'agent' ? 'Support Specialist' : 'Customer')}</div>
        <div>${m.text}</div>
        <div class="chat-bubble-meta">
          <span>${m.channel || 'Web Portal'}</span>
          <span>${m.timestamp}</span>
        </div>
      </div>
    `).join("");
    stream.scrollTop = stream.scrollHeight;

    // Telephony Audio Call Transcript
    const trans = document.getElementById("commTelephonyTranscript");
    if (trans) {
      trans.innerHTML = (data.call_transcript || []).map(call => `
        <div style="margin-bottom: 12px; font-size: 0.84rem; line-height: 1.5;">
          <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:var(--text-muted); font-weight:700;">
            <span style="color:${call.speaker === 'Agent' ? 'var(--primary)' : '#059669'};">${call.speaker}</span>
            <span>${call.time}</span>
          </div>
          <div style="color:var(--text-heading); margin-top:2px;">${call.text}</div>
        </div>
      `).join("");
    }

    // AI Recommended Draft
    const draft = document.getElementById("commAiDraftText");
    if (draft) draft.value = data.ai_recommended_draft || "";

  } catch (e) {
    console.error("Error selecting comm thread:", e);
  }
}

async function sendCommunicationReply() {
  SoundFX.playClick();
  if (!selectedCommComplaintId) return;
  const input = document.getElementById("commReplyInput");
  const msg = input.value.trim();
  if (!msg) return;

  const formData = new FormData();
  formData.append("complaint_id", selectedCommComplaintId);
  formData.append("message", msg);
  formData.append("channel", "Email / Web Ticket");

  try {
    const res = await fetch("/api/communication/send", { method: "POST", body: formData });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      input.value = "";
      selectCommunicationThread(selectedCommComplaintId);
      showToast("Official reply dispatched to customer", "success");
    }
  } catch (e) {
    showToast("Error sending reply: " + e, "danger");
  }
}

function insertCannedReply(text) {
  SoundFX.playClick();
  const input = document.getElementById("commReplyInput");
  if (input) {
    input.value = text;
    input.focus();
  }
}

function applyAiDraftToInput() {
  SoundFX.playClick();
  const draft = document.getElementById("commAiDraftText");
  const input = document.getElementById("commReplyInput");
  if (draft && input) {
    input.value = draft.value;
    input.focus();
    showToast("AI Draft inserted into response editor", "info");
  }
}

// -------------------------------------------------------------
// 12. REFUNDS & ESCROW TREASURY
// -------------------------------------------------------------
async function loadRefundsDashboard() {
  try {
    const res = await fetch("/api/refunds/summary");
    const data = await res.json();
    currentRefundRecords = data.records || [];

    const m = data.metrics || {};
    document.getElementById("kpiTotalClaims").innerText = `$ ${m.total_claims_val.toLocaleString()}`;
    document.getElementById("kpiEscrowHeld").innerText = `$ ${m.escrow_held_val.toLocaleString()}`;
    document.getElementById("kpiApprovedPayouts").innerText = `$ ${m.approved_payout_val.toLocaleString()}`;
    document.getElementById("kpiDisputedClaims").innerText = `$ ${m.disputed_val.toLocaleString()}`;

    renderRefundsTable(currentRefundRecords);
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading refunds:", e);
  }
}

function renderRefundsTable(records) {
  const tbody = document.getElementById("refundsTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:var(--text-muted);">No refund records matching current filter.</td></tr>`;
    return;
  }

  records.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${r.complaint_id}</td>
      <td>
        <div style="font-weight: 800; color: var(--text-heading);">${r.customer_name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.order_reference}</div>
      </td>
      <td><strong style="color: var(--text-heading); font-size: 1rem;">$ ${r.amount.toFixed(2)}</strong></td>
      <td><span class="badge ${r.escrow_status.includes('Paid') ? 'badge-success' : (r.escrow_status.includes('Held') ? 'badge-primary' : 'badge-danger')}">${r.escrow_status}</span></td>
      <td><span class="badge ${r.refund_eligible ? 'badge-success' : 'badge-secondary'}">${r.refund_eligible ? 'Eligible' : 'Ineligible'}</span></td>
      <td><span style="font-family:'JetBrains Mono', monospace; font-size:0.8rem;">${r.policy_matched}</span></td>
      <td>
        <button class="pill-tab active" style="padding: 5px 14px; font-size: 0.78rem;" onclick="openRefundActionModal('${r.complaint_id}', ${r.amount})">
          Settle &rarr;
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterRefundTable(tab) {
  SoundFX.playClick();
  document.querySelectorAll(".tab-pills-row .pill-tab").forEach(btn => btn.classList.remove("active"));
  if (event && event.target) {
    event.target.classList.add("active");
  }

  if (tab === "All") {
    renderRefundsTable(currentRefundRecords);
  } else if (tab === "Held in Escrow") {
    renderRefundsTable(currentRefundRecords.filter(r => r.escrow_status.includes("Held")));
  } else if (tab === "Released / Paid") {
    renderRefundsTable(currentRefundRecords.filter(r => r.escrow_status.includes("Paid") || r.escrow_status.includes("Released")));
  } else if (tab === "Disputed") {
    renderRefundsTable(currentRefundRecords.filter(r => r.escrow_status.includes("Dispute") || !r.refund_eligible));
  }
}

function filterRefundSearch() {
  const input = document.getElementById("refundSearchInput");
  if (!input) return;
  const q = input.value.toLowerCase();
  const filtered = currentRefundRecords.filter(r => 
    r.complaint_id.toLowerCase().includes(q) ||
    r.customer_name.toLowerCase().includes(q) ||
    r.order_reference.toLowerCase().includes(q) ||
    r.policy_matched.toLowerCase().includes(q)
  );
  renderRefundsTable(filtered);
}

// 💰 AI Smart Escrow & CLV Optimizer
async function openRefundActionModal(cid, amt) {
  SoundFX.playClick();
  const modal = document.getElementById("refundActionModal");
  if (!modal) return;
  document.getElementById("refundModalComplaintId").value = cid;
  document.getElementById("refundModalAmount").value = amt;
  const sub = document.getElementById("modalRefundSubtitle");
  if (sub) sub.innerText = `${cid} | Financial Dispute Claim ($ ${amt.toFixed(2)})`;

  modal.style.display = "flex";

  // Fetch CLV Optimizer telemetry
  try {
    const res = await fetch(`/api/escrow/clv-optimizer/${cid}`);
    const data = await res.json();

    const churnBadge = document.getElementById("clvChurnBadge");
    if (churnBadge) churnBadge.innerText = `Churn Risk: ${data.churn_risk_pct}%`;

    const optA = document.getElementById("optACashAmt");
    if (optA) optA.innerText = `$ ${data.option_a_cash.toFixed(2)}`;

    const optB = document.getElementById("optBVoucherAmt");
    if (optB) optB.innerText = `$ ${data.option_b_voucher.toFixed(2)}`;

    const rec = document.getElementById("clvStrategyRec");
    if (rec) rec.innerText = `AI Recommendation: ${data.recommendation}`;
  } catch (e) {
    console.warn("CLV Optimizer fetch:", e);
  }
}

function closeRefundActionModal() {
  SoundFX.playClick();
  const modal = document.getElementById("refundActionModal");
  if (modal) modal.style.display = "none";
}

async function submitRefundExecution() {
  SoundFX.playClick();
  const cid = document.getElementById("refundModalComplaintId").value;
  const amt = document.getElementById("refundModalAmount").value;
  const action = document.getElementById("refundModalAction").value;
  const method = document.getElementById("refundModalMethod").value;
  const note = document.getElementById("refundModalNote").value;

  const formData = new FormData();
  formData.append("complaint_id", cid);
  formData.append("action", action);
  formData.append("amount", amt);
  formData.append("payment_method", method);
  formData.append("reviewer_notes", note);

  try {
    const res = await fetch("/api/refunds/process", { method: "POST", body: formData });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      closeRefundActionModal();
      loadRefundsDashboard();
      showToast(`Escrow transaction executed for ${cid}! Payout authorized.`, "success");
    }
  } catch (e) {
    showToast("Error processing refund payout: " + e, "danger");
  }
}

// -------------------------------------------------------------
// 13. ANALYTICS & REPORTS (CHART.JS + 50-PRODUCT DEFECT RADAR)
// -------------------------------------------------------------
async function loadAnalyticsDashboard() {
  try {
    const res = await fetch("/api/analytics/metrics");
    const data = await res.json();

    const kpiTot = document.getElementById("kpiTotal");
    if (kpiTot) kpiTot.innerText = data.total_complaints || "525";

    // Category Doughnut Chart
    const catCtx = document.getElementById("categoryChart");
    if (catCtx) {
      new Chart(catCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(data.categories || {}),
          datasets: [{
            data: Object.values(data.categories || {}),
            backgroundColor: ["var(--cream, #eef0d0)", "var(--cream, #eef0d0)", "var(--cream, #eef0d0)", "#10b981", "#f59e0b", "#f43f5e"]
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: "bottom" } }
        }
      });
    }

    // Urgency Bar Chart
    const urgCtx = document.getElementById("urgencyChart");
    if (urgCtx) {
      new Chart(urgCtx, {
        type: "bar",
        data: {
          labels: Object.keys(data.urgencies || {}),
          datasets: [{
            label: "Volume",
            data: Object.values(data.urgencies || {}),
            backgroundColor: ["#10b981", "#0ea5e9", "#f59e0b", "#f43f5e"]
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } }
        }
      });
    }

    // 📊 Load 50-Product Defect Radar & Recall Advisory
    loadDefectRadar();
  } catch (e) {
    console.error("Error loading analytics charts:", e);
  }
}

async function loadDefectRadar() {
  try {
    const res = await fetch("/api/analytics/defect-radar");
    const data = await res.json();

    // Recall Advisory Banner
    if (data.recall_advisory && data.recall_advisory.advisory_active) {
      const banner = document.getElementById("aiRecallAdvisoryBanner");
      if (banner) {
        banner.style.display = "block";
        document.getElementById("recallAdvisoryTitle").innerText = `Executive QA Advisory: ${data.recall_advisory.affected_models.join(", ")} Defect Alert`;
        document.getElementById("recallAdvisoryDesc").innerText = data.recall_advisory.recommended_action;
      }
    }

    // Defect Radar Table
    const tbody = document.getElementById("defectRadarTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const products = data.monitored_products || [];
    products.forEach(p => {
      const tr = document.createElement("tr");
      const statusClass = p.failure_count > 10 ? "badge-danger" : (p.failure_count > 5 ? "badge-warning" : "badge-success");
      const statusText = p.failure_count > 10 ? "Critical QA" : (p.failure_count > 5 ? "Elevated" : "Nominal");

      tr.innerHTML = `
        <td style="font-weight:800; font-family:'JetBrains Mono', monospace; color:var(--primary);">${p.product_id}</td>
        <td><strong style="color:var(--text-heading);">${p.name}</strong></td>
        <td><span class="badge badge-primary">${p.category}</span></td>
        <td><strong>$ ${p.price.toFixed(2)}</strong></td>
        <td><span style="font-weight:800; color:${p.failure_count > 8 ? '#e11d48' : 'var(--text-heading)'};">${p.failure_count} Reports</span></td>
        <td style="color:var(--text-body); font-size:0.85rem;">${p.primary_failure_mode}</td>
        <td>
          <div style="display:flex; align-items:center; gap:8px;">
            <div class="progress-bar-container" style="width:70px; margin-bottom:0;">
              <div class="progress-bar-fill" style="width:${p.quality_index}%; background:${p.quality_index > 80 ? '#10b981' : '#f59e0b'};"></div>
            </div>
            <span style="font-size:0.8rem; font-weight:700;">${p.quality_index}%</span>
          </div>
        </td>
        <td><span class="badge ${statusClass}">${statusText}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Error loading defect radar:", e);
  }
}

// -------------------------------------------------------------
// 14. ADMIN PROFILE & RBAC USER MANAGEMENT
// -------------------------------------------------------------

function openProfileSettingsModal() {
  SoundFX.playClick();
  const modal = document.getElementById("profileSettingsModal");
  if (modal) modal.style.display = "flex";
}

function closeProfileSettingsModal() {
  const modal = document.getElementById("profileSettingsModal");
  if (modal) modal.style.display = "none";
}

async function handleSaveProfile(e) {
  e.preventDefault();
  SoundFX.playClick();
  const display_name = document.getElementById("editDisplayName").value.trim();
  const username = document.getElementById("editUsername").value.trim();
  const password = document.getElementById("editPassword").value.trim();
  const phone = document.getElementById("editPhone").value.trim();
  const avatar = document.getElementById("editAvatarUrl").value.trim();
  const btn = document.getElementById("saveProfileBtn");

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const payload = { display_name, username, phone, avatar };
    if (password) payload.password = password;

    const res = await fetch("/api/auth/update-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok && data.success) {
      SoundFX.playSuccess();
      showToast("Profile credentials updated successfully!", "success");
      closeProfileSettingsModal();
      
      const avatarImg = document.getElementById("topbarAvatarImg");
      if (avatarImg && data.user.avatar) avatarImg.src = data.user.avatar;
      const userName = document.getElementById("topbarUserName");
      if (userName && data.user.display_name) userName.innerHTML = `${data.user.display_name} <span style="font-size:0.72rem; color:var(--primary); font-weight:800;">(${data.user.role.toUpperCase()})</span>`;
    } else {
      showToast(data.detail || "Error updating credentials", "danger");
    }
  } catch (err) {
    showToast("Network error: " + err, "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Changes';
  }
}

function openAdminUsersModal() {
  SoundFX.playClick();
  const modal = document.getElementById("adminUsersModal");
  if (modal) {
    modal.style.display = "flex";
    loadAdminUsers();
  }
}

function closeAdminUsersModal() {
  const modal = document.getElementById("adminUsersModal");
  if (modal) modal.style.display = "none";
}

async function loadAdminUsers() {
  const tbody = document.getElementById("adminUsersTableBody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Loading registered users...</td></tr>`;

  try {
    const res = await fetch("/api/admin/users");
    if (!res.ok) {
      if (res.status === 403) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: #ef4444;"><i class="fa-solid fa-lock" style="margin-right: 6px;"></i> Admin permissions required to view registered users & RBAC roles. Please sign in as Admin.</td></tr>`;
        return;
      }
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: #ef4444;"><i class="fa-solid fa-triangle-exclamation" style="margin-right: 6px;"></i> Failed to load registered users feed (HTTP ${res.status}).</td></tr>`;
      return;
    }
    const data = await res.json();
    const users = data.users || [];

    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--text-muted);">No registered users found in system.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 10px;">
            <img src="${u.avatar || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(u.display_name || u.username) + '&background=4285F4&color=fff'}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary);">
            <div>
              <strong style="color: var(--text-heading); font-size: 0.92rem;">${u.display_name || u.username}</strong>
              <div style="font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${u.user_id}</div>
            </div>
          </div>
        </td>
        <td style="font-size: 0.88rem; color: var(--text-body);">${u.email || '-'}</td>
        <td><span class="user-mono-tag">${u.username || '-'}</span></td>
        <td>
          <span class="badge ${u.role === 'admin' ? 'badge-danger' : (u.role === 'agent' ? 'badge-warning' : 'badge-primary')}">
            ${(u.role || 'customer').toUpperCase()}
          </span>
        </td>
        <td>
          <span style="font-size: 0.8rem; font-weight: 700; color: ${u.auth_provider === 'google' ? '#ea4335' : 'var(--text-heading)'}; display: inline-flex; align-items: center; gap: 5px;">
            <i class="fa-${u.auth_provider === 'google' ? 'brands fa-google' : 'solid fa-key'}"></i>
            ${(u.auth_provider || 'local').toUpperCase()}
          </span>
        </td>
        <td>
          <span style="font-weight: 800; font-family: monospace; color: #10b981;">${u.complaints_count || 0} Tickets</span>
        </td>
        <td style="font-size: 0.78rem; color: var(--text-muted);">${u.created_at || '-'}</td>
        <td>
          <select onchange="updateUserRole('${u.user_id}', this.value)" style="background: var(--glass-bg-subtle); border: 1px solid var(--glass-border); padding: 4px 8px; border-radius: 8px; font-size: 0.78rem; font-weight: 700; color: var(--text-heading); cursor: pointer;">
            <option value="customer" ${u.role === 'customer' ? 'selected' : ''}>Customer</option>
            <option value="agent" ${u.role === 'agent' ? 'selected' : ''}>Support Agent</option>
            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin Superuser</option>
          </select>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #e11d48; padding: 20px;">Error loading users: ${err}</td></tr>`;
  }
}

async function updateUserRole(userId, newRole) {
  SoundFX.playClick();
  try {
    const res = await fetch(`/api/admin/users/${userId}/role`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: newRole })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      SoundFX.playSuccess();
      showToast(`User role updated to ${newRole.toUpperCase()}!`, "success");
      loadAdminUsers();
    } else {
      showToast(data.detail || "Failed to update role", "danger");
    }
  } catch (err) {
    showToast("Error updating role: " + err, "danger");
  }
}

function toggleRoleSwitchMenu() {
  const m = document.getElementById("roleSwitchMenu");
  if (m) m.style.display = m.style.display === "none" ? "block" : "none";
}

async function quickSwitchStaffRole(role) {
  let username = "admin";
  let pwd = "admin123";
  let target = "/admin";
  if (role === "agent") {
    username = "agent";
    pwd = "agent123";
    target = "/agent";
  } else if (role === "warranty_manager") {
    username = "warranty_manager";
    pwd = "warranty123";
    target = "/warranty";
  }
  
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: username, password: pwd })
    });
    window.location.href = target;
  } catch (e) {
    window.location.href = target;
  }
}

document.addEventListener("click", (e) => {
  const menu = document.getElementById("roleSwitchMenu");
  if (menu && menu.style.display === "block" && !e.target.closest("#roleSwitchMenu") && !e.target.closest("button[onclick='toggleRoleSwitchMenu()']")) {
    menu.style.display = "none";
  }
});

// -------------------------------------------------------------
// 15. TOP 1% STAT COUNTER & SKELETON LOADER ANIMATIONS
// -------------------------------------------------------------
function animateCountUp(el, targetNum, duration = 1000, prefix = "", suffix = "") {
  if (!el) return;
  const start = 0;
  const startTime = performance.now();
  
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // easeOutQuart curve
    const easeProgress = 1 - Math.pow(1 - progress, 4);
    const current = Math.floor(start + (targetNum - start) * easeProgress);
    el.textContent = `${prefix}${current.toLocaleString()}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.textContent = `${prefix}${targetNum.toLocaleString()}${suffix}`;
    }
  }
  requestAnimationFrame(update);
}

function renderTableSkeleton(tbodyId, columns = 8, rows = 5) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  
  let html = "";
  for (let r = 0; r < rows; r++) {
    html += "<tr>";
    for (let c = 0; c < columns; c++) {
      const width = Math.floor(40 + Math.random() * 50);
      html += `<td style="padding: 16px;"><span class="skeleton-box" style="width: ${width}%; height: 16px;"></span></td>`;
    }
    html += "</tr>";
  }
  tbody.innerHTML = html;
}

document.addEventListener("DOMContentLoaded", () => {
  // Stagger entrance on cards
  const cards = document.querySelectorAll(".summary-card, .metrics-grid");
  cards.forEach(c => c.classList.add("stagger-container"));

  // Trigger stat count-up for static KPI values
  const kpiVals = document.querySelectorAll(".summary-card-value");
  kpiVals.forEach(val => {
    const text = val.textContent.trim();
    const match = text.match(/^([^\d]*)([\d,.]+)(.*)$/);
    if (match) {
      const prefix = match[1];
      const num = parseFloat(match[2].replace(/,/g, ''));
      const suffix = match[3];
      if (!isNaN(num) && num > 0) {
        animateCountUp(val, num, 1100, prefix, suffix);
      }
    }
  });
});

