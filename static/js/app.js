// =============================================================
// SupportNova / ResponseX - Ultra High Quality Frontend Engine
// =============================================================

// Global state
let currentComplaints = [];
let selectedComplaintId = null;
let selectedCommComplaintId = null;
let currentCommThreads = [];
let currentRefundRecords = [];
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
  let saved = "dark";
  try {
    const stored = localStorage.getItem("supportnova_theme") || localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") saved = stored;
  } catch (error) {
    saved = "dark";
  }
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  SoundFX.playClick();
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("supportnova_theme", next); } catch (error) {}
  updateThemeIcon(next);
  updateChartTheme();
  showToast(`Theme switched to ${next === 'dark' ? 'Obsidian Cyber Glass' : 'Crystal Light Glass'}`, "info");
}

function getChartPalette() {
  return document.documentElement.getAttribute("data-theme") === "light"
    ? ["#0f766e", "#1d4ed8", "#b45309", "#be123c", "#6d28d9", "#0369a1", "#047857", "#a16207", "#9d174d", "#4338ca", "#4d7c0f", "#475569"]
    : ["#34d399", "#60a5fa", "#fbbf24", "#fb7185", "#a78bfa", "#38bdf8", "#4ade80", "#facc15", "#f472b6", "#818cf8", "#a3e635", "#94a3b8"];
}

function updateChartTheme() {
  if (typeof Chart === "undefined" || !Chart.instances) return;
  const light = document.documentElement.getAttribute("data-theme") === "light";
  const textColor = light ? "#334155" : "#e2e8f0";
  const gridColor = light ? "rgba(51, 65, 85, 0.14)" : "rgba(226, 232, 240, 0.14)";
  Object.values(Chart.instances).forEach(chart => {
    if (chart.options.plugins?.legend?.labels) chart.options.plugins.legend.labels.color = textColor;
    Object.values(chart.options.scales || {}).forEach(scale => {
      if (scale.ticks) scale.ticks.color = textColor;
      if (scale.grid) scale.grid.color = gridColor;
    });
    chart.update("none");
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[char]);
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
        <div style="display:flex; align-items:center; gap:10px;"><i class="fa-solid fa-table-cells-large" style="color:var(--cream, #eef0d0);"></i><span>All Complaints Queue</span></div>
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
  if (document.body?.dataset.userRole === "judge") {
    const statusPill = document.getElementById("liveStreamPill");
    const statusText = document.getElementById("liveStatusText");
    if (statusText) statusText.innerText = "Read-only mode";
    if (statusPill) {
      statusPill.style.background = "rgba(148, 163, 184, 0.14)";
      statusPill.style.color = "var(--text-secondary)";
    }
    return;
  }

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
          <div style="font-weight: 800; color: var(--text-heading);">${escapeHtml(msg.customer_name || "Customer")}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">Standard Tier</div>
        </td>
        <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; color: var(--text-heading);">
          <span style="color:var(--cream, #eef0d0); font-weight:800;">[NEW] </span>${escapeHtml(msg.complaint_title || "Untitled complaint")}
        </td>
        <td><span class="badge badge-secondary">${escapeHtml(msg.category || 'General')}</span></td>
        <td style="font-size: 0.825rem; font-weight: 600;">Customer Care</td>
        <td><span class="badge ${msg.urgency === 'Critical' ? 'badge-danger' : 'badge-primary'}">${escapeHtml(msg.urgency || 'Medium')}</span></td>
        <td><strong style="color: var(--text-heading);">${escapeHtml(msg.priority || 'P2')}</strong></td>
        <td><span class="badge badge-secondary">Awaiting analysis</span></td>
        <td>
          <button class="pill-tab" style="padding: 5px 14px; font-size: 0.78rem;">
            Triage &rarr;
          </button>
        </td>
      `;
      const triageButton = tr.querySelector("button");
      if (triageButton) triageButton.addEventListener("click", (event) => {
        event.stopPropagation();
        openTriageModal(msg.complaint_id);
      });
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

  const iconEl = document.createElement("i");
  iconEl.className = `fa-solid ${icon}`;
  iconEl.style.cssText = `font-size:1.25rem;color:${iconColor};`;
  const messageEl = document.createElement("div");
  messageEl.style.cssText = "flex-grow:1;font-size:0.88rem;font-weight:700;color:var(--text-heading);";
  messageEl.textContent = message;
  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Dismiss notification");
  closeButton.textContent = "×";
  closeButton.style.cssText = "background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.1rem;opacity:0.7;";
  closeButton.addEventListener("click", () => toast.remove());
  const progress = document.createElement("div");
  progress.className = "toast-progress-bar";
  progress.style.background = barColor;
  toast.append(iconEl, messageEl, closeButton, progress);

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
  if (document.getElementById("agentThroughputCount") || document.getElementById("agentQueuePending")) {
    loadAgentStats();
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

async function loadAgentStats() {
  const fields = {
    agentThroughputCount: "— cases",
    agentAvgTime: "Not recorded",
    agentAccuracy: "Not measured",
    agentQueuePending: "— pending",
    agentCriticalCount: "—"
  };
  try {
    const response = await fetch("/api/agent/stats", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Stats request failed (${response.status})`);
    const data = await response.json();
    fields.agentThroughputCount = `${data.resolved_cases ?? 0} cases`;
    fields.agentAvgTime = data.avg_inspection_time || "Not recorded";
    fields.agentAccuracy = Number.isFinite(data.accuracy_pct) ? `${data.accuracy_pct}%` : "Not measured";
    fields.agentQueuePending = `${data.pending_reviews ?? 0} pending`;
    fields.agentCriticalCount = String(data.critical_alerts ?? 0);
  } catch (error) {
    console.error("Unable to load agent dashboard metrics", error);
  }
  Object.entries(fields).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  });
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
  document.getElementById("heroCustomerPhone").innerText = c.customer_phone || "Not recorded";
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

    const compStatus = c.comparison?.verification_status || "Awaiting analysis";
    const compClass = compStatus === "Verified" ? "badge-success" : (compStatus.includes("Warning") ? "badge-warning" : (compStatus === "Awaiting analysis" ? "badge-secondary" : "badge-danger"));

    tr.innerHTML = `
      <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${escapeHtml(c.complaint_id)}</td>
      <td>
        <div style="font-weight: 800; color: var(--text-heading);">${escapeHtml(c.customer_name)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">${escapeHtml(c.customer_type || 'Standard')} Tier</div>
      </td>
      <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600; color: var(--text-heading);">
        ${c.is_adversarial ? '<span style="color:#e11d48; font-weight:800;">🛡️ [Adversarial] </span>' : ''}
        ${(c.is_duplicate || c.is_repeat_complaint) ? '<span style="color:#d97706; font-weight:800;">🔁 [Repeat] </span>' : ''}
        ${escapeHtml(c.complaint_title)}
      </td>
      <td><span class="badge badge-secondary">${escapeHtml(c.genai_analysis?.category || 'Not analyzed')}</span></td>
      <td style="font-size: 0.825rem; font-weight: 600;">${escapeHtml(c.department || 'Not assigned')}</td>
      <td><span class="badge ${c.urgency === 'Critical' ? 'badge-danger' : (c.urgency === 'High' ? 'badge-warning' : 'badge-primary')}">${escapeHtml(c.urgency || 'Not assessed')}</span></td>
      <td><strong style="color: var(--text-heading);">${escapeHtml(c.priority || 'Not assigned')}</strong></td>
      <td><span class="badge ${compClass}">${escapeHtml(compStatus)}</span></td>
      <td>
        <button class="pill-tab" style="padding: 5px 14px; font-size: 0.78rem;" onclick="event.stopPropagation(); openTriageModal('${c.complaint_id}')">
          Triage &rarr;
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterByTab(tab, clickEvent) {
  SoundFX.playClick();
  document.querySelectorAll(".tab-pills-row .pill-tab").forEach(btn => btn.classList.remove("active"));
  const activeTab = clickEvent?.currentTarget || document.querySelector(`.tab-pills-row .pill-tab[onclick*="'${tab}'"]`);
  if (activeTab) activeTab.classList.add("active");

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
    const vision = data.vision_analysis || null;
    const visionCard = document.getElementById("modalVisionAssessment");
    if (visionCard) {
      visionCard.style.display = vision ? "block" : "none";
      if (vision) {
        document.getElementById("modalVisionIssue").textContent = vision.visible_issue || "Not assessed";
        document.getElementById("modalVisionSeverity").textContent = vision.severity || "Unclear";
        document.getElementById("modalVisionSafety").textContent = vision.potential_safety_hazard === true ? "Possible hazard — urgent staff verification" : "No hazard identified by model; staff verification still required";
        document.getElementById("modalVisionNextStep").textContent = vision.recommended_next_step || "Manual image review";
        document.getElementById("modalVisionReviewNote").textContent = vision.review_note || "This AI summary is advisory and does not determine warranty coverage.";
        const observations = document.getElementById("modalVisionObservations");
        observations.replaceChildren(...(vision.observations || []).map(text => {
          const item = document.createElement("li");
          item.textContent = text;
          return item;
        }));
      }
    }

    // 🧠 Customer Emotion & Frustration Heatmap Rendering
    const sent = data.sentiment_telemetry || {};
    const frScore = typeof sent.frustration_score === "number" && Number.isFinite(sent.frustration_score) ? Math.max(0, Math.min(100, sent.frustration_score)) : null;
    const emState = sent.emotion_state || "Not analyzed";
    const triggers = Array.isArray(sent.key_emotional_triggers) ? sent.key_emotional_triggers : [];

    const emCard = document.getElementById("modalEmotionCard");
    const emStateEl = document.getElementById("modalEmotionState");
    const frScoreEl = document.getElementById("modalFrustrationScore");
    const frBarEl = document.getElementById("modalFrustrationBar");
    const trChipsEl = document.getElementById("modalTriggerChips");

    if (emStateEl) emStateEl.innerText = emState;
    if (frScoreEl) frScoreEl.innerText = frScore === null ? "Not measured" : `${frScore}% / 100`;
    if (frBarEl) {
      frBarEl.style.width = frScore === null ? "0%" : `${frScore}%`;
      if (frScore !== null) frBarEl.style.background = frScore > 70 ? 'linear-gradient(90deg, #f59e0b, #e11d48)' : 'linear-gradient(90deg, #10b981, #f59e0b)';
    }
    if (trChipsEl) {
      trChipsEl.innerHTML = triggers.map(t => `<span class="trigger-chip"><i class="fa-solid fa-fire"></i> ${escapeHtml(t)}</span>`).join("") || '<span class="text-muted">No triggers recorded</span>';
    }

    // Adversarial Banner
    const advBanner = document.getElementById("modalAdversarialBanner");
    if (advBanner && data.genai_analysis && data.genai_analysis.adversarial_warning) {
      advBanner.style.display = "block";
      advBanner.innerText = `🛡️ SECURITY WARNING: ${data.genai_analysis.adversarial_warning}`;
    } else if (advBanner) {
      advBanner.style.display = "none";
    }

    // Comparison summary
    const comp = data.comparison || {};
    const vBadge = document.getElementById("modalVerificationStatus");
    if (vBadge) {
      vBadge.innerText = comp.verification_status || "Manual review required";
      vBadge.className = `badge ${comp.verification_status === 'Verified' ? 'badge-success' : (comp.verification_status?.includes('Warning') ? 'badge-warning' : 'badge-danger')}`;
    }
    
    ["modalCoverageScore", "modalTraceabilityScore", "modalConsistencyScore"].forEach((id, index) => {
      const el = document.getElementById(id);
      const score = [comp.mandatory_coverage_score, comp.source_traceability_score, comp.consistency_score][index];
      if (el) el.innerText = typeof score === "number" && Number.isFinite(score) ? `${score}%` : "Not measured";
    });

    // Pipeline 1: GenAI
    const ai = data.genai_analysis || {};
    const aiFields = document.getElementById("modalGenAiFields");
    const gtFields = document.getElementById("modalGroundTruthFields");
    ["genaiCategory", "genaiSubcategory", "genaiDept", "genaiUrgency", "genaiPriority", "genaiPolicy", "genaiEscalation"].forEach((id, i) => {
      const el = document.getElementById(id);
      const values = [ai.category, ai.subcategory, ai.recommended_department, ai.urgency, ai.priority, ai.referenced_policy_id, ai.escalation_required === undefined ? "Not analyzed" : (ai.escalation_required ? `Yes (${ai.escalation_tier || "tier not set"})` : "No")];
      if (el) el.innerText = values[i] || "Not analyzed";
    });

    const stepsUl = document.getElementById("genaiStepsList");
    if (stepsUl) stepsUl.innerHTML = (ai.resolution_steps || []).map(s => `<li>${escapeHtml(s)}</li>`).join("") || "<li>Unavailable — review this case manually.</li>";
    const responseEl = document.getElementById("genaiCustomerResponse") || document.getElementById("modalCustomerResponseDraft");
    if (responseEl) responseEl.value = ai.customer_response || "";

    // Pipeline 2: Ground Truth
    const gt = data.ground_truth || {};
    ["gtRuleId", "gtDept", "gtEscalation", "gtTier", "gtPolicy", "gtRefund"].forEach((id, i) => {
      const el = document.getElementById(id);
      const values = [gt.rule_id_matched, gt.expected_department, gt.mandatory_escalation === undefined ? "Not evaluated" : (gt.mandatory_escalation ? "YES (MANDATORY)" : "No"), gt.escalation_tier, gt.applicable_policy_id ? `${gt.applicable_policy_id} (${gt.policy_status || "status unavailable"})` : null, gt.refund_eligible === undefined ? "Not evaluated" : (gt.refund_eligible ? "ELIGIBLE" : "NOT ELIGIBLE")];
      if (el) el.innerText = values[i] || "Not evaluated";
    });

    const gtStepsUl = document.getElementById("gtMandatoryStepsList");
    if (gtStepsUl) gtStepsUl.innerHTML = (gt.mandatory_resolution_steps || []).map(s => `<li>${escapeHtml(s)}</li>`).join("") || "<li>No required steps recorded.</li>";
    if (aiFields) aiFields.innerHTML = `<div>Category: ${escapeHtml(ai.category || "Not analyzed")}</div><div>Subcategory: ${escapeHtml(ai.subcategory || "Not analyzed")}</div><div>Department: ${escapeHtml(ai.recommended_department || "Not analyzed")}</div><div>Urgency: ${escapeHtml(ai.urgency || "Not analyzed")}</div><div>Priority: ${escapeHtml(ai.priority || "Not analyzed")}</div><div>Policy: ${escapeHtml(ai.referenced_policy_id || "Not analyzed")}</div><div>Resolution: ${escapeHtml((ai.resolution_steps || []).join("; ") || "Manual review required")}</div>`;
    if (gtFields) gtFields.innerHTML = `<div>Rule: ${escapeHtml(gt.rule_id_matched || "Not evaluated")}</div><div>Department: ${escapeHtml(gt.expected_department || "Not evaluated")}</div><div>Escalation: ${gt.mandatory_escalation ? "Required" : "Not required / not evaluated"}</div><div>Tier: ${escapeHtml(gt.escalation_tier || "Not evaluated")}</div><div>Policy: ${escapeHtml(gt.applicable_policy_id || "Not evaluated")}</div><div>Refund: ${gt.refund_eligible === undefined ? "Not evaluated" : (gt.refund_eligible ? "Eligible" : "Not eligible")}</div>`;

    const probDiv = document.getElementById("gtProhibitedActions");
    if (probDiv && comp.unauthorized_promise_detected) {
      probDiv.innerHTML = `<strong>VIOLATION:</strong> ${escapeHtml((comp.unsupported_claims_flagged || []).join("; "))}`;
    } else if (probDiv && data.comparison) {
      probDiv.innerText = "Zero policy violations detected in GenAI response.";
    } else if (probDiv) {
      probDiv.innerText = "No GenAI comparison is available; review manually.";
    }

    const clarBox = document.getElementById("clarificationQuestionsBox");
    if (clarBox) {
      if (!data.order_id || !data.product_or_service || String(data.complaint_description || "").length < 40) {
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
  const respEl = document.getElementById("genaiCustomerResponse") || document.getElementById("modalCustomerResponseDraft");
  if (!respEl) return;
  const current = respEl.value.trim();
  if (!current) { showToast("No response draft is available to reformat.", "warning"); return; }
  const body = current.replace(/^(Dear|Hello|Hi).*?\n\n/i, "").replace(/\n\n(Sincerely|Regards|Best regards),?[\s\S]*$/i, "").trim();
  const greeting = tone === "Formal" ? "Dear Customer," : (tone === "Concise" ? "Hello," : "Hello,");
  const closing = tone === "Formal" ? "Respectfully,\nSupport Team" : "Kind regards,\nSupport Team";
  respEl.value = `${greeting}\n\n${body}\n\n${closing}`;
  showToast(`Response draft updated to ${tone} tone`, "info");
}

function generateFollowUpTemplate(type) {
  const respEl = document.getElementById("genaiCustomerResponse") || document.getElementById("modalCustomerResponseDraft");
  if (!respEl) return;
  const ref = selectedComplaintId ? ` ${selectedComplaintId}` : "";
  if (type === "request_info") {
    respEl.value = `Hello,\n\nTo continue reviewing your case${ref}, please share any missing order details and supporting information relevant to the issue. Please do not send full payment-card details.\n\nKind regards,\nSupport Team`;
  } else if (type === "resolution_confirm") {
    respEl.value = `Hello,\n\nWe have updated the review record for your case${ref}. A support representative will confirm any next steps separately.\n\nKind regards,\nSupport Team`;
  } else if (type === "refund_update") {
    respEl.value = `Hello,\n\nYour refund request${ref} is being reviewed. No payment has been initiated through this system. We will provide an update after the decision is confirmed.\n\nKind regards,\nSupport Team`;
  } else if (type === "replacement_eta") {
    respEl.value = `Hello,\n\nYour replacement request${ref} is under review. We will share shipment details only after an order and carrier confirmation are available.\n\nKind regards,\nSupport Team`;
  } else if (type === "case_closure") {
    respEl.value = `Hello,\n\nIf your case${ref} has been resolved, please confirm that the outcome works for you. If the issue remains, reply with any additional details so we can continue the review.\n\nKind regards,\nSupport Team`;
  }
  showToast("Follow-up template inserted", "success");
}

async function saveAgentResolution() {
  const responseDraft = document.getElementById("modalCustomerResponseDraft")?.value || "";
  const formData = new FormData();
  formData.append("action", "approve");
  formData.append("reviewer_notes", "Agent review recorded. Draft has not been sent to the customer.");
  formData.append("response_draft", responseDraft);
  try {
    const res = await fetch(`/api/complaints/${selectedComplaintId}/triage`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Review could not be recorded.");
    showToast("Review recorded; the draft was not sent.", "success");
    closeTriageModal();
    loadComplaints();
  } catch (error) {
    showToast(error.message, "danger");
  }
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
    if (!res.ok) throw new Error(`Knowledge Base request failed (${res.status}).`);
    const data = await res.json();
    const tbody = document.getElementById("knowledgeTableBody");
    if (!tbody) return;
    const docs = data.documents || [];
    tbody.replaceChildren();
    const activeCount = docs.filter(doc => (doc.status || "Active") === "Active").length;
    const activeCountEl = document.getElementById("activePolicyCount");
    const chunksCountEl = document.getElementById("totalChunksCount");
    const versionSummaryEl = document.getElementById("policyVersionSummary");
    if (activeCountEl) activeCountEl.textContent = `${activeCount} Active`;
    if (chunksCountEl) chunksCountEl.textContent = `${Number(data.total_chunks) || 0} Chunks`;
    if (versionSummaryEl) {
      const versions = [...new Set(docs.map(doc => doc.version).filter(Boolean))];
      versionSummaryEl.textContent = versions.length ? versions.join(", ") : "No versions recorded";
    }
    if (docs.length === 0) {
      const row = tbody.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 8;
      cell.textContent = "No knowledge documents indexed.";
      cell.style.cssText = "text-align:center; padding:20px; color:var(--text-muted);";
      return;
    }

    docs.forEach(doc => {
      const tr = document.createElement("tr");
      const cell = (value, className = "") => {
        const td = tr.insertCell();
        if (className) td.className = className;
        td.textContent = value == null || value === "" ? "Not recorded" : String(value);
        return td;
      };
      const idCell = cell(doc.document_id);
      idCell.style.cssText = "font-weight:800; font-family:'JetBrains Mono',monospace; color:var(--text-heading);";
      const titleCell = cell(doc.title || doc.filename);
      titleCell.style.fontWeight = "700";
      cell(doc.doc_type || "Policy / SOP");
      cell(doc.version);
      cell(doc.status || "Active");
      cell(Number.isFinite(Number(doc.precedence_score)) ? doc.precedence_score : "Not calculated");
      cell(`${Number(doc.total_chunks) || 0} Chunks`);
      const actionCell = tr.insertCell();
      const inspectButton = document.createElement("button");
      inspectButton.className = "pill-tab";
      inspectButton.style.cssText = "padding:5px 14px; font-size:0.78rem;";
      inspectButton.textContent = "Inspect →";
      inspectButton.addEventListener("click", () => inspectPolicy(doc.document_id));
      actionCell.appendChild(inspectButton);
      tbody.appendChild(tr);
    });
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading knowledge docs:", e);
    ["activePolicyCount", "totalChunksCount", "policyVersionSummary"].forEach(id => {
      const element = document.getElementById(id);
      if (element) element.textContent = "Unavailable";
    });
    const tbody = document.getElementById("knowledgeTableBody");
    if (tbody) {
      const row = tbody.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 8;
      cell.textContent = "Knowledge Base records could not be loaded. Please try again.";
      cell.style.cssText = "text-align:center; padding:20px; color:var(--text-muted);";
    }
  }
}

async function inspectPolicy(docId) {
  SoundFX.playClick();
  const modal = document.getElementById("policyInspectModal") || document.getElementById("policyModal");
  if (!modal) return;
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/knowledge/document/${docId}`);
    if (!res.ok) throw new Error(`Document request failed (${res.status}).`);
    const data = await res.json();

    // Support both ID naming schemes
    const titleEl = document.getElementById("inspectDocTitle") || document.getElementById("modalPolicyTitle");
    if (titleEl) titleEl.textContent = data.title || docId;

    const statusEl = document.getElementById("inspectDocStatus");
    if (statusEl) {
      const status = data.status || "Not recorded";
      statusEl.textContent = status;
      statusEl.className = `badge ${status === "Active" ? "badge-success" : status === "Superseded" ? "badge-warning" : "badge-primary"}`;
    }

    const subEl = document.getElementById("inspectDocSubtitle") || document.getElementById("modalPolicyDocId");
    if (subEl) subEl.textContent = `Document ID: ${data.document_id || "Not recorded"} | Version: ${data.version || "Not recorded"}`;

    const catEl = document.getElementById("inspectDocCategory") || document.getElementById("modalPolicyCategory");
    if (catEl) catEl.textContent = data.category || "General";

    const countEl = document.getElementById("inspectDocChunkCount") || document.getElementById("modalPolicyChunksCount");
    if (countEl) countEl.innerText = `${(data.chunks || []).length} Traceable Chunks`;

    const precedenceEl = document.getElementById("inspectDocPrecedence");
    if (precedenceEl) precedenceEl.textContent = data.precedence_score == null ? "Not calculated" : String(data.precedence_score);
    const filenameEl = document.getElementById("inspectDocFilename");
    if (filenameEl) filenameEl.textContent = data.filename || "Not recorded";

    const chunksCont = document.getElementById("inspectChunksList") || document.getElementById("modalPolicyChunks");
    if (chunksCont) {
      chunksCont.replaceChildren();
      (data.chunks || []).forEach((chunk, index) => {
        const card = document.createElement("div");
        card.style.cssText = "background:var(--glass-bg-subtle); border:1px solid var(--glass-border); border-radius:var(--radius-sm); padding:18px; margin-bottom:14px;";
        const heading = document.createElement("div");
        heading.style.cssText = "display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;";
        const chunkLabel = document.createElement("strong");
        chunkLabel.style.cssText = "font-family:'JetBrains Mono',monospace; color:var(--primary); font-size:0.85rem;";
        chunkLabel.textContent = `Chunk #${index + 1}: ${chunk.chunk_id || `CHK-${index + 1}`}`;
        const sectionLabel = document.createElement("span");
        sectionLabel.className = "badge badge-primary";
        sectionLabel.style.fontSize = "0.75rem";
        sectionLabel.textContent = `Clause Section ${chunk.section_number || index + 1}`;
        heading.append(chunkLabel, sectionLabel);
        const content = document.createElement("p");
        content.style.cssText = "font-size:0.92rem; color:var(--text-body); line-height:1.6; white-space:pre-wrap;";
        content.textContent = chunk.content || chunk.text_content || chunk.clause_text || "No extracted text available.";
        card.append(heading, content);
        chunksCont.appendChild(card);
      });
    }
  } catch (e) {
    console.error("Error inspecting policy:", e);
    const chunksCont = document.getElementById("inspectChunksList") || document.getElementById("modalPolicyChunks");
    if (chunksCont) chunksCont.textContent = "This document could not be loaded. Close this window and try again.";
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
  cont.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.95rem;"><i class="fa-solid fa-spinner fa-spin"></i> Scanning cross-clause policy contradictions...</div>`;

  try {
    const res = await fetch("/api/knowledge/conflicts");
    if (!res.ok) throw new Error(`Audit request failed (${res.status}).`);
    const data = await res.json();
    const conflicts = data.conflicts || [];
    const auditCount = document.getElementById("policyAuditFindingCount");
    const summary = {
      auditPolicyCount: data.total_policies_scanned,
      auditChunkCount: data.total_chunks_evaluated,
      auditRuleCount: data.total_rules_cross_referenced,
      auditScore: data.governance_health_score == null ? "Not measured" : `${data.governance_health_score}%`
    };
    Object.entries(summary).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value == null ? "0" : String(value);
    });
    if (auditCount) auditCount.textContent = `${conflicts.length} finding${conflicts.length === 1 ? "" : "s"}`;

    if (conflicts.length === 0) {
      cont.textContent = "No metadata or rule-reference findings were identified. This audit does not evaluate semantic contradictions between policy text.";
      cont.style.cssText = "text-align:center; padding:30px; color:var(--text-muted); font-weight:600;";
      return;
    }

    cont.replaceChildren();
    conflicts.forEach(conflict => {
      const card = document.createElement("div");
      card.style.cssText = `background:var(--glass-bg-subtle); border:1px solid var(--glass-border); border-left:4px solid ${conflict.severity === "HIGH" ? "#e11d48" : "#f59e0b"}; border-radius:var(--radius-sm); padding:18px 22px;`;
      const title = document.createElement("strong");
      title.textContent = `${conflict.conflict_id || "Finding"} — ${conflict.category || "Review"} • ${conflict.topic || ""}`;
      const findingText = document.createElement("p");
      findingText.style.margin = "12px 0";
      findingText.textContent = `${conflict.clause_a_ref || "Source"}: ${conflict.clause_a_text || ""} ${conflict.clause_b_ref || "Compared record"}: ${conflict.clause_b_text || ""}`;
      const resolution = document.createElement("p");
      resolution.textContent = `${conflict.resolution_guideline || "Review this finding."} ${conflict.precedence_winner ? `Winner: ${conflict.precedence_winner}` : ""}`;
      card.append(title, findingText, resolution);
      cont.appendChild(card);
    });
  } catch (e) {
    cont.textContent = `Error scanning policies: ${e.message || e}`;
    cont.style.cssText = "color:#e11d48; text-align:center; padding:20px;";
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
    if (!res.ok || !data.success) {
      throw new Error(data.detail || `Upload failed (${res.status}).`);
    }
    if (data.success) {
      SoundFX.playSuccess();
      showToast(`Document indexed successfully! ${data.chunks_created} chunks generated.`, "success");
      document.getElementById("uploadPolicyModal").style.display = "none";
      form.reset();
      await loadKnowledgeList();
    }
  } catch (err) {
    showToast("Error uploading policy: " + (err.message || err), "danger");
  }
}

// -------------------------------------------------------------
// 10. RULES MATRIX (DETERMINISTIC COMPLAINT RULES)
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
      const polId = r.policy_id || r.applicable_policy_id || "Not specified";
      const compMax = (r.max_compensation_usd !== undefined && r.max_compensation_usd !== null) 
        ? `$${r.max_compensation_usd}` 
        : (r.compensation_max ?? "Not specified");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: #059669;">${escapeHtml(r.rule_id || 'Unassigned')}</td>
        <td><strong style="color: var(--text-heading);">${escapeHtml(r.category || 'Not specified')}</strong></td>
        <td>${escapeHtml(r.subcategory || 'Not specified')}</td>
        <td><span class="badge badge-primary">${escapeHtml(r.department || 'Not specified')}</span></td>
        <td><span class="badge ${r.urgency === 'Critical' ? 'badge-danger' : 'badge-warning'}">${escapeHtml(r.urgency || 'Not specified')}</span></td>
        <td><span style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; font-weight:700; color:var(--primary);">${escapeHtml(polId)}</span></td>
        <td>${r.mandatory_escalation ? '<span class="badge badge-danger">MANDATORY</span>' : '<span class="badge badge-secondary">No</span>'}</td>
        <td>${r.refund_eligible ? '<span class="badge badge-success">Eligible</span>' : '<span class="badge badge-secondary">No</span>'}</td>
        <td style="font-family:'JetBrains Mono', monospace; font-weight:700; color:#10b981;">${escapeHtml(compMax)}</td>
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
  formData.append("message_text", msg);
  formData.append("channel", "Email / Web Ticket");

  try {
    const res = await fetch("/api/communication/send", { method: "POST", body: formData });
    const data = await res.json();
    if (data.success) {
      SoundFX.playSuccess();
      input.value = "";
      selectCommunicationThread(selectedCommComplaintId);
      showToast("Reply saved to the case thread. Email delivery is not connected.", "success");
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
    if (!res.ok) throw new Error(`Refund records unavailable (${res.status})`);
    const data = await res.json();
    currentRefundRecords = data.records || [];

    const m = data.metrics || {};
    [["kpiTotalClaims", m.total_claims_val], ["kpiEscrowHeld", m.escrow_held_val], ["kpiApprovedPayouts", m.approved_payout_val], ["kpiDisputedClaims", m.disputed_val]].forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.innerText = Number.isFinite(Number(value)) ? `$ ${Number(value).toLocaleString()}` : "Not recorded";
    });

    renderRefundsTable(currentRefundRecords);
    init3DCardTilt();
  } catch (e) {
    console.error("Error loading refunds:", e);
    ["kpiTotalClaims", "kpiEscrowHeld", "kpiApprovedPayouts", "kpiDisputedClaims"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerText = "Unavailable";
    });
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
      <td style="font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${escapeHtml(r.complaint_id)}</td>
      <td>
        <div style="font-weight: 800; color: var(--text-heading);">${escapeHtml(r.customer_name)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(r.order_reference)}</div>
      </td>
      <td><strong style="color: var(--text-heading); font-size: 1rem;">${r.amount !== null && r.amount !== "" && Number.isFinite(Number(r.amount)) ? `$ ${Number(r.amount).toFixed(2)}` : "Not verified"}</strong></td>
      <td><span class="badge ${r.escrow_status.includes('Paid') ? 'badge-success' : (r.escrow_status.includes('Held') ? 'badge-primary' : 'badge-secondary')}">${escapeHtml(r.escrow_status)}</span></td>
      <td><span class="badge ${r.refund_eligible ? 'badge-success' : 'badge-secondary'}">${r.refund_eligible ? 'Eligible' : 'Ineligible'}</span></td>
      <td><span style="font-family:'JetBrains Mono', monospace; font-size:0.8rem;">${escapeHtml(r.policy_matched)}</span></td>
      <td>
        <button class="pill-tab active" style="padding: 5px 14px; font-size: 0.78rem;" ${r.amount !== null && r.amount !== "" && Number.isFinite(Number(r.amount)) && r.refund_eligible ? `onclick="openRefundActionModal('${escapeHtml(r.complaint_id)}', ${Number(r.amount)})"` : "disabled title=\"Verified amount and eligibility are required\""}>
          Review &rarr;
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterRefundTable(tab, clickEvent) {
  SoundFX.playClick();
  document.querySelectorAll(".tab-pills-row .pill-tab").forEach(btn => btn.classList.remove("active"));
  const activeTab = clickEvent?.currentTarget || document.querySelector(`.tab-pills-row .pill-tab[onclick*="'${tab}'"]`);
  if (activeTab) activeTab.classList.add("active");

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
  if (!Number.isFinite(Number(amt)) || Number(amt) <= 0) {
    showToast("A verified transaction amount is required before recording a payout decision.", "warning");
    return;
  }
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
    if (churnBadge) churnBadge.innerText = "Not available";
    const optA = document.getElementById("optACashAmt");
    if (optA) optA.innerText = "Not verified";
    const optB = document.getElementById("optBVoucherAmt");
    if (optB) optB.innerText = "Not available";
    const rec = document.getElementById("clvStrategyRec");
    if (rec) rec.innerText = data.reason || "A validated transaction and approved retention model are not connected.";
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
      showToast(`Decision recorded for ${cid}; no payment was sent.`, "success");
    } else {
      showToast(data.detail || "Decision could not be recorded.", "danger");
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
    if (kpiTot) kpiTot.innerText = data.total_complaints ?? "—";
    const kpiCompliance = document.getElementById("kpiCompliance");
    if (kpiCompliance) kpiCompliance.innerText = data.checked_count ? `${data.compliance_rate}%` : "—";

    // Category Doughnut Chart
    const catCtx = document.getElementById("categoryChart");
    if (catCtx) {
      Chart.getChart(catCtx)?.destroy();
      new Chart(catCtx, {
        type: "doughnut",
        data: {
          labels: Object.keys(data.categories || {}),
          datasets: [{
            data: Object.values(data.categories || {}),
            backgroundColor: getChartPalette()
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: "bottom", labels: { color: document.documentElement.dataset.theme === "light" ? "#334155" : "#e2e8f0" } } }
        }
      });
    }

    // Urgency Bar Chart
    const urgCtx = document.getElementById("urgencyChart");
    if (urgCtx) {
      Chart.getChart(urgCtx)?.destroy();
      new Chart(urgCtx, {
        type: "bar",
        data: {
          labels: Object.keys(data.urgencies || {}),
          datasets: [{
            label: "Volume",
            data: Object.values(data.urgencies || {}),
            backgroundColor: getChartPalette()
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, tooltip: { enabled: true } },
          scales: { x: { ticks: { color: document.documentElement.dataset.theme === "light" ? "#334155" : "#e2e8f0" }, grid: { color: document.documentElement.dataset.theme === "light" ? "rgba(51,65,85,.14)" : "rgba(226,232,240,.14)" } }, y: { beginAtZero: true, ticks: { color: document.documentElement.dataset.theme === "light" ? "#334155" : "#e2e8f0" }, grid: { color: document.documentElement.dataset.theme === "light" ? "rgba(51,65,85,.14)" : "rgba(226,232,240,.14)" } } }
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
    if (!res.ok) throw new Error(`Product complaint summary failed (${res.status}).`);
    const data = await res.json();
    const tbody = document.getElementById("defectRadarTableBody");
    if (!tbody) return;
    tbody.replaceChildren();
    const catalogCount = document.getElementById("radarCatalogCount");
    const matchedCount = document.getElementById("radarMatchedCount");
    const unmatchedCount = document.getElementById("radarUnmatchedCount");
    if (catalogCount) catalogCount.textContent = `${Number(data.catalog_product_count) || 0} catalog products`;
    if (matchedCount) matchedCount.textContent = String(Number(data.complaints_matched_to_catalog) || 0);
    if (unmatchedCount) unmatchedCount.textContent = String(Number(data.complaints_without_catalog_match) || 0);

    const products = data.monitored_products || [];
    if (!products.length) {
      const row = tbody.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 6;
      cell.textContent = "No product catalog records are available.";
      return;
    }
    products.forEach(product => {
      const tr = document.createElement("tr");
      const values = [
        product.product_id,
        product.name,
        product.category,
        Number.isFinite(Number(product.price)) ? `$${Number(product.price).toFixed(2)}` : "Not recorded",
        `${Number(product.complaint_count) || 0}`,
        product.primary_mention_type || "Unspecified",
      ];
      values.forEach((value, index) => {
        const cell = tr.insertCell();
        cell.textContent = value == null || value === "" ? "Not recorded" : String(value);
        if (index === 0) cell.style.cssText = "font-weight:800; font-family:'JetBrains Mono',monospace; color:var(--primary);";
        if (index === 1) cell.style.fontWeight = "700";
      });
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Error loading defect radar:", e);
    const tbody = document.getElementById("defectRadarTableBody");
    if (tbody) {
      tbody.replaceChildren();
      const row = tbody.insertRow();
      const cell = row.insertCell();
      cell.colSpan = 6;
      cell.textContent = "Product complaint summary could not be loaded.";
    }
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
