function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.style.position = "fixed";
    container.style.bottom = "24px";
    container.style.right = "24px";
    container.style.zIndex = "99999";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "10px";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `custom-toast toast-${type}`;
  toast.style.background = type === "danger" ? "#be123c" : (type === "success" ? "#047857" : (type === "warning" ? "#854d0e" : "var(--primary)"));
  toast.style.color = "#ffffff";
  toast.style.padding = "12px 22px";
  toast.style.borderRadius = "12px";
  toast.style.fontSize = "0.88rem";
  toast.style.fontWeight = "700";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.2)";
  toast.style.display = "flex";
  toast.style.alignItems = "center";
  toast.style.gap = "10px";
  toast.style.animation = "fadeIn 0.3s ease";
  const icon = document.createElement("i");
  icon.className = `fa-solid ${type === 'danger' ? 'fa-triangle-exclamation' : (type === 'success' ? 'fa-circle-check' : 'fa-circle-info')}`;
  const label = document.createElement("span");
  label.textContent = message;
  toast.append(icon, label);
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

let productsCatalog = [];
let isVoiceRecording = false;
let speechRecognizer = null;
let currentAuthUser = null;

document.addEventListener("DOMContentLoaded", () => {
  load50Products();
  const desc = document.getElementById("complaintDescriptionInput");
  if (desc) updateCharCount(desc);
  initSpeechRecognition();
  checkCustomerAuthState();
});

async function checkCustomerAuthState() {
  try {
    const res = await fetch("/api/auth/me");
    const data = await res.json();
    if (data.authenticated && data.user) {
      currentAuthUser = data.user;
      const badge = document.getElementById("myComplaintsBadge");
      if (badge) badge.innerText = data.total_complaints || 0;
      const nameInput = document.getElementById("formCustomerName");
      const emailInput = document.getElementById("formCustomerEmail");
      const phoneInput = document.getElementById("formCustomerPhone");
      if (nameInput && !nameInput.value) nameInput.value = data.user.display_name || data.user.username;
      if (emailInput && !emailInput.value) emailInput.value = data.user.email;
      if (phoneInput && !phoneInput.value && data.user.phone) phoneInput.value = data.user.phone;
    }
  } catch (e) {
    console.error(e);
  }
}

function triggerCustomerGoogleLogin() {
  window.location.href = "/login";
}

function openCustomerGoogleModal() {
  const modal = document.getElementById("googleAuthModal");
  if (modal) modal.style.display = "flex";
}

function closeCustomerGoogleModal() {
  const modal = document.getElementById("googleAuthModal");
  if (modal) modal.style.display = "none";
}

function selectCustomerQuickGoogleAccount(email, name) {
  document.getElementById("custGoogleEmailInput").value = email;
  document.getElementById("custGoogleNameInput").value = name;
  submitCustomerDirectGoogleAuth();
}

async function submitCustomerDirectGoogleAuth() {
  const email = document.getElementById("custGoogleEmailInput").value.trim();
  const name = document.getElementById("custGoogleNameInput").value.trim();
  if (!email) {
    showToast("Please enter a valid Gmail address.", "warning");
    return;
  }
  closeCustomerGoogleModal();

  try {
    const res = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Welcome, ${data.user.display_name}! Successfully logged in.`, "success");
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.detail || "Google authentication failed.", "danger");
    }
  } catch (err) {
    showToast("Network error: " + err, "danger");
  }
}

function openCustomerProfileModal() {
  const modal = document.getElementById("customerProfileModal");
  if (modal) modal.style.display = "flex";
}

function closeCustomerProfileModal() {
  const modal = document.getElementById("customerProfileModal");
  if (modal) modal.style.display = "none";
}

async function handleCustomerProfileSave(e) {
  e.preventDefault();
  const display_name = document.getElementById("custModalName").value.trim();
  const username = document.getElementById("custModalUsername").value.trim();
  const password = document.getElementById("custModalPassword").value.trim();
  const phone = document.getElementById("custModalPhone").value.trim();
  const btn = document.getElementById("custProfileSaveBtn");

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const payload = { display_name, username, phone };
    if (password) payload.password = password;

    const res = await fetch("/api/auth/update-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Profile updated successfully!", "success");
      closeCustomerProfileModal();
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.detail || "Error updating profile.", "danger");
    }
  } catch (err) {
    showToast("Network error: " + err, "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Settings';
  }
}

// -------------------------------------------------------------
// Products Catalog Loading & Auto-fill
// -------------------------------------------------------------
async function load50Products() {
  try {
    const res = await fetch("/api/products");
    const data = await res.json();
    productsCatalog = data.products || [];
    
    const dropdown = document.getElementById("productSelectDropdown");
    if (!dropdown) return;

    productsCatalog.forEach(p => {
      const opt = document.createElement("option");
      opt.value = `${p.product_id}: ${p.product_name}`;
      opt.innerText = `[${p.product_id}] ${p.product_name} (${p.category}) - ${p.price}`;
      dropdown.appendChild(opt);
    });
  } catch (e) {
    console.error("Error loading products catalog:", e);
  }
}

function onProductSelectChange(e) {
  const val = e.target.value;
  const badge = document.getElementById("selectedProductBadge");
  if (!val) {
    badge.style.display = "none";
    return;
  }

  const pid = val.split(":")[0].trim();
  const prod = productsCatalog.find(p => p.product_id === pid);
  if (prod) {
    badge.style.display = "flex";
    document.getElementById("badgeProductName").innerText = prod.product_name;
    document.getElementById("badgeProductId").innerText = prod.product_id;
    document.getElementById("badgeProductCategory").innerText = prod.category;
    document.getElementById("badgeProductWarranty").innerText = prod.warranty;

    const iconEl = document.getElementById("badgeCategoryIcon");
    if (iconEl) {
      if (prod.category.includes("Laptop")) iconEl.className = "fa-solid fa-laptop";
      else if (prod.category.includes("Phone") || prod.category.includes("Smartphone")) iconEl.className = "fa-solid fa-mobile-screen-button";
      else if (prod.category.includes("Audio") || prod.category.includes("Headphones")) iconEl.className = "fa-solid fa-headphones";
      else if (prod.category.includes("Smart Home") || prod.category.includes("Home")) iconEl.className = "fa-solid fa-house-signal";
      else if (prod.category.includes("Wearable") || prod.category.includes("Watch")) iconEl.className = "fa-solid fa-clock";
      else iconEl.className = "fa-solid fa-microchip";
    }
  } else {
    badge.style.display = "none";
  }
  updateStepIndicators();
  triggerRulePreview();
}

function updateCharCount(el) {
  const lbl = document.getElementById("charCountLabel");
  if (lbl) {
    lbl.innerText = `${el.value.length} characters`;
  }
  updateStepIndicators();
}

function updateStepIndicators() {
  const name = document.getElementById("formCustomerName")?.value.trim();
  const prod = document.getElementById("productSelectDropdown")?.value;
  const desc = document.getElementById("complaintDescriptionInput")?.value.trim();
  
  const step1 = document.getElementById("stepIndicator1");
  const step2 = document.getElementById("stepIndicator2");
  const step3 = document.getElementById("stepIndicator3");
  const step4 = document.getElementById("stepIndicator4");

  if (step1) step1.classList.add("active");
  if (step2) step2.classList.toggle("active", Boolean(name && prod));
  if (step3) step3.classList.toggle("active", Boolean(prod && desc && desc.length > 20));
  if (step4) step4.classList.toggle("active", Boolean(desc && desc.length > 50));
}

function goToStep(stepNum) {
  if (stepNum === 1) {
    document.getElementById("formCustomerName")?.focus();
  } else if (stepNum === 2) {
    document.getElementById("productSelectDropdown")?.focus();
  } else if (stepNum === 3) {
    document.getElementById("complaintDescriptionInput")?.focus();
  } else if (stepNum === 4) {
    triggerRulePreview();
    document.getElementById("submitFormBtn")?.scrollIntoView({ behavior: "smooth" });
  }
}

// -------------------------------------------------------------
// 1. 🎙️ REAL-TIME VOICE DICTATION (Web Speech API)
// -------------------------------------------------------------
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;
  
  speechRecognizer = new SpeechRecognition();
  speechRecognizer.continuous = true;
  speechRecognizer.interimResults = true;
  speechRecognizer.lang = "en-US";

  speechRecognizer.onresult = (event) => {
    let interim = "";
    let finalTranscript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + " ";
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    const desc = document.getElementById("complaintDescriptionInput");
    if (desc) {
      if (finalTranscript) desc.value += finalTranscript;
      updateCharCount(desc);
      triggerRulePreview();
    }
  };

  speechRecognizer.onerror = (e) => {
    console.error("Speech recognition error:", e);
    stopVoiceDictation();
  };
}

function toggleVoiceDictation() {
  if (!isVoiceRecording) {
    startVoiceDictation();
  } else {
    stopVoiceDictation();
  }
}

function startVoiceDictation() {
  if (!speechRecognizer) {
    showToast("Speech recognition is not supported in this browser. Please use Chrome or Edge.", "warning");
    return;
  }
  try {
    speechRecognizer.start();
    isVoiceRecording = true;
    const btn = document.getElementById("voiceMicBtn");
    const text = document.getElementById("voiceMicText");
    if (btn) btn.classList.add("voice-pulse-active");
    if (text) text.innerText = "Listening... (Click to Stop)";
  } catch (err) {
    console.error(err);
  }
}

function stopVoiceDictation() {
  if (speechRecognizer && isVoiceRecording) {
    speechRecognizer.stop();
    isVoiceRecording = false;
    const btn = document.getElementById("voiceMicBtn");
    const text = document.getElementById("voiceMicText");
    if (btn) btn.classList.remove("voice-pulse-active");
    if (text) text.innerText = "Voice Dictation";
  }
}

// -------------------------------------------------------------
// 2. 👁️ MULTIMODAL VISION FORENSIC SCANNER
// -------------------------------------------------------------
async function handleVisionImageUpload(input) {
  if (!input.files || !input.files[0]) {
    updateEvidenceConsent();
    return;
  }
  const file = input.files[0];
  const status = document.getElementById("visionUploadStatus");
  const preview = document.getElementById("visionAnalysisBox");
  if (file.size > 10 * 1024 * 1024) {
    input.value = "";
    if (status) status.textContent = "That image exceeds the 10 MB limit.";
    updateEvidenceConsent();
    return;
  }
  if (!/^image\/(jpeg|png|webp|gif)$/.test(file.type)) {
    input.value = "";
    if (status) status.textContent = "Choose a JPEG, PNG, WebP, or GIF image.";
    updateEvidenceConsent();
    return;
  }
  if (status) status.textContent = `${file.name} selected (${(file.size / 1024 / 1024).toFixed(1)} MB). It will be analyzed only when you submit the complaint.`;
  const removeButton = document.getElementById("removeEvidenceImage");
  if (removeButton) removeButton.style.display = "inline-flex";
  if (preview) {
    preview.textContent = "Visual notes will appear in the staff case record after submission. AI analysis is advisory and may require manual review.";
    preview.style.display = "block";
  }
  updateEvidenceConsent();
}

function clearEvidenceImage() {
  const input = document.getElementById("complaintEvidenceImage");
  const status = document.getElementById("visionUploadStatus");
  const preview = document.getElementById("visionAnalysisBox");
  const removeButton = document.getElementById("removeEvidenceImage");
  if (input) input.value = "";
  if (status) status.textContent = "Optional; maximum 10 MB. The original photo is not retained.";
  if (preview) { preview.style.display = "none"; preview.textContent = ""; }
  if (removeButton) removeButton.style.display = "none";
  updateEvidenceConsent();
}

function updateEvidenceConsent() {
  const image = document.getElementById("complaintEvidenceImage");
  const consent = document.getElementById("evidenceProcessingConsent");
  if (consent) consent.required = Boolean(image?.files?.length);
}

let preCheckTimer = null;
function triggerRulePreview() {
  clearTimeout(preCheckTimer);
  preCheckTimer = setTimeout(async () => {
    const title = document.getElementById("complaintTitleInput")?.value.trim() || "";
    const desc = document.getElementById("complaintDescriptionInput")?.value.trim() || "";
    const tier = document.getElementById("customerTierSelect").value;

    if (!title || !desc) {
      const box = document.getElementById("aiPreCheckBox");
      if (box) box.style.display = "none";
      return;
    }

    const formData = new FormData();
    formData.append("complaint_title", title);
    formData.append("complaint_description", desc);
    formData.append("customer_type", tier);

    try {
      const res = await fetch("/api/complaints/pre-check", { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Intake preview failed (${res.status}).`);
      const data = await res.json();

      const box = document.getElementById("aiPreCheckBox");
      if (!box) return;
      box.style.display = "block";

      const categoryBadge = document.getElementById("preCheckCategoryBadge");
      const sla = document.getElementById("preCheckSla");
      const refund = document.getElementById("preCheckRefund");
      const advisory = document.getElementById("preCheckAdvisory");
      if (categoryBadge) categoryBadge.textContent = `${data.estimated_category} (${data.estimated_priority})`;
      if (sla) sla.textContent = data.estimated_sla;
      if (refund) refund.textContent = data.refund_eligibility_preview ? "Potentially eligible — verification required" : "Eligibility not established; staff review required";
      if (advisory) advisory.textContent = data.safety_advisory;
      
      const sent = data.sentiment || {};
      const frustration = document.getElementById("preCheckFrustration");
      if (frustration) frustration.textContent = typeof sent.frustration_score === "number" && Number.isFinite(sent.frustration_score) ? `${sent.frustration_score}% heuristic estimate (${sent.emotion_state || 'Unclassified'})` : "Not measured";

    } catch (e) {
      console.error("Error running rule-based intake preview:", e);
    }
  }, 400);
}

// -------------------------------------------------------------
// 4. MULTILINGUAL TRANSLATION SWITCHER
// -------------------------------------------------------------
function changePortalLanguage(lang) {
  const dict = {
    "ur": {
      "title": "صارفین کی شکایات اور وارنٹی حل کا مرکز",
      "sub": "اپنی شکایت درج کریں، اس کی صورتِ حال دیکھیں، اور معاون براؤزر میں آواز سے متن لکھیں۔"
    },
    "ar": {
      "title": "مركز خدمة العملاء وحل النزاعات والضمان",
      "sub": "قدّم شكواك وتابع حالتها. يمكن استخدام الإملاء الصوتي إذا كان متاحاً في المتصفح."
    },
    "es": {
      "title": "Centro de Resolución de Garantías y Reclamaciones",
      "sub": "Envíe su queja y consulte su estado. Use el dictado si su navegador lo admite."
    },
    "en": {
      "title": "Customer Complaint & Warranty Resolution Center",
      "sub": "Submit and track hardware complaints, describe the issue, and use voice dictation where your browser supports it."
    }
  };

  const current = dict[lang] || dict["en"];
  document.getElementById("heroTitleText").innerText = current.title;
  document.getElementById("heroSubtitleText").innerText = current.sub;
}

function rateSatisfaction(stars) {
  const btns = document.querySelectorAll("#ratingStars button");
  btns.forEach((b, idx) => {
    b.style.color = idx < stars ? "#f59e0b" : "var(--text-muted)";
  });
  showToast(`Thank you for rating our resolution team with ${stars} Star(s)!`, "success");
}

function switchPortalTab(tab) {
  const submitBtn = document.getElementById("tabSubmitBtn");
  const chatBtn = document.getElementById("tabChatBtn");
  const myComplaintsBtn = document.getElementById("tabMyComplaintsBtn");
  const trackBtn = document.getElementById("tabTrackBtn");
  
  const submitSec = document.getElementById("submitSection");
  const chatSec = document.getElementById("chatSection");
  const myComplaintsSec = document.getElementById("myComplaintsSection");
  const trackSec = document.getElementById("trackSection");

  [submitBtn, chatBtn, myComplaintsBtn, trackBtn].forEach(b => {
    if (!b) return;
    b.classList.remove("active");
    b.setAttribute("aria-selected", "false");
  });
  [submitSec, chatSec, myComplaintsSec, trackSec].forEach(s => {
    if (!s) return;
    s.style.display = "none";
    s.setAttribute("hidden", "hidden");
  });

  const show = (button, section) => {
    if (button) {
      button.classList.add("active");
      button.setAttribute("aria-selected", "true");
    }
    if (section) {
      section.style.display = "block";
      section.removeAttribute("hidden");
      requestAnimationFrame(() => section.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  };

  if (tab === "submit") {
    show(submitBtn, submitSec);
  } else if (tab === "chat") {
    show(chatBtn, chatSec);
    loadCustChatMessages();
  } else if (tab === "my-complaints") {
    show(myComplaintsBtn, myComplaintsSec);
    loadMyComplaints();
  } else {
    show(trackBtn, trackSec);
  }

  if (tab !== "chat" && custChatPollTimer) {
    clearInterval(custChatPollTimer);
    custChatPollTimer = null;
  }
}

let custChatPollTimer = null;

async function loadCustChatMessages() {
  const box = document.getElementById("custChatMsgBox");
  if (!box) return;
  box.setAttribute("aria-busy", "true");
  try {
    const res = await fetch("/api/chat/live/messages?client_id=USR-CUSTOMER");
    if (!res.ok) throw new Error(`Chat service returned ${res.status}`);
    const data = await res.json();
    const msgs = data.messages || [];
    renderCustChatBubbles(msgs);
    box.removeAttribute("aria-busy");
    if (custChatPollTimer) clearInterval(custChatPollTimer);
    custChatPollTimer = setInterval(async () => {
      try {
        const r = await fetch("/api/chat/live/messages?client_id=USR-CUSTOMER");
        const d = await r.json();
        renderCustChatBubbles(d.messages || []);
      } catch (e) {}
    }, 3500);
  } catch (e) {
    box.removeAttribute("aria-busy");
    box.innerHTML = `<div style="align-self:center; text-align:center; color:var(--text-muted); padding:24px;">Chat is temporarily unavailable. Please try again in a moment.</div>`;
    console.error("Error loading customer chat:", e);
  }
}

function formatChatText(text) {
  if (text.startsWith("![image](")) {
    const url = text.substring(9, text.length - 1);
    return `<img src="${url}" style="max-width:240px;max-height:240px;border-radius:12px;margin-top:4px;display:block;box-shadow:0 4px 12px rgba(0,0,0,0.15);">`;
  }
  if (text.startsWith("[file](")) {
    const parts = text.substring(7, text.length - 1).split("|");
    const url = parts[0];
    const name = parts[1] || "Document";
    return `<a href="${url}" target="_blank" style="color:inherit;text-decoration:underline;display:inline-flex;align-items:center;gap:6px;font-weight:700;"><i class="fa-solid fa-file-arrow-down"></i> ${name}</a>`;
  }
  return escapeHTML(text);
}

function renderCustChatBubbles(msgs) {
  const box = document.getElementById("custChatMsgBox");
  if (!box) return;
  box.innerHTML = `<div style="align-self: center; font-size: 0.72rem; color: var(--text-muted); background: var(--glass-bg-subtle); border: 1px solid var(--glass-border); padding: 4px 14px; border-radius: 9999px;">🔒 Encrypted Channel with Support Team</div>`;
  msgs.forEach(m => {
    const isCust = m.sender === "customer";
    const text = m.message || m.content || "";
    const contentHtml = formatChatText(text);
    const wrap = document.createElement("div");
    wrap.style.cssText = `display: flex; flex-direction: column; ${isCust ? "align-self: flex-end; max-width: 78%;" : "align-self: flex-start; max-width: 78%;"}`;
    if (isCust) {
      wrap.innerHTML = `<div style="background: var(--cream); color: var(--ink, #101010); font-weight: 500; padding: 10px 16px; border-radius: 16px 16px 3px 16px; font-size: 0.88rem; box-shadow: 0 4px 14px rgba(0,0,0,0.35);">${contentHtml}</div><div style="font-size: 0.64rem; color: var(--text-muted); text-align: right; margin-top: 3px;">${m.timestamp || ""}</div>`;
    } else {
      wrap.innerHTML = `<div style="background: var(--glass-bg); backdrop-filter: blur(12px); border: 1px solid var(--glass-border); color: var(--text-heading); padding: 10px 16px; border-radius: 3px 16px 16px 16px; font-size: 0.88rem; box-shadow: 0 4px 14px rgba(0,0,0,0.06);">${contentHtml}</div><div style="font-size: 0.64rem; color: var(--text-muted); margin-top: 3px;">${m.sender_name || "Support Officer"} &bull; ${m.timestamp || ""}</div>`;
    }
    box.appendChild(wrap);
  });
  box.scrollTop = box.scrollHeight;
}

async function uploadCustChatFile(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fetch("/api/chat/upload-file", { method: "POST", body: fd });
    const data = await res.json();
    if (data.success) {
      let msgText = "";
      if (data.is_image) {
        msgText = `![image](${data.file_url})`;
      } else {
        msgText = `[file](${data.file_url}|${data.filename})`;
      }
      await fetch("/api/chat/live/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msgText, client_id: "USR-CUSTOMER", sender: "customer", sender_name: "Valued Customer" })
      });
      loadCustChatMessages();
    }
  } catch (e) {}
  input.value = "";
}

async function sendCustChatMessage() {
  const inp = document.getElementById("custChatInput");
  if (!inp) return;
  const text = inp.value.trim();
  if (!text) return;
  inp.value = "";
  try {
    const res = await fetch("/api/chat/live/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, client_id: "USR-CUSTOMER", sender: "customer", sender_name: "Valued Customer" })
    });
    const d = await res.json();
    if (d.success && d.message) {
      loadCustChatMessages();
    }
  } catch (e) {}
}

let clientCallId = null;
let clientCallPollInterval = null;

function stopClientCallRequest(message = "Call request closed.") {
  if (clientCallPollInterval) clearInterval(clientCallPollInterval);
  clientCallPollInterval = null;
  clientCallId = null;
  const modal = document.getElementById("snVoiceCallBackdrop");
  if (modal) modal.style.display = "none";
  if (message) showToast(message, "info");
}

async function startClientVoiceCall() {
  try {
    const res = await fetch("/api/call/initiate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.status === "unavailable") {
      showToast("No support staff are online to receive a request right now.", "warning");
    } else if (data.status === "ringing") {
      clientCallId = data.call_id;
      const modal = document.getElementById("snVoiceCallBackdrop");
      if (modal) {
        document.getElementById("snCallName").textContent = data.target_staff?.name || "Support team";
        document.getElementById("snCallSub").textContent = data.target_staff?.role || "Customer support";
        document.getElementById("snCallStatusText").textContent = "REQUEST SENT — AUDIO NOT CONNECTED";
        document.getElementById("snCallStatusText").style.color = "#fbbf24";
        const actions = document.getElementById("snCallActionRow");
        if (actions) actions.innerHTML = '<button class="sn-call-btn-circle sn-call-btn-decline" onclick="stopClientCallRequest()" title="Close request"><i class="fa-solid fa-xmark"></i></button>';
        modal.style.display = "flex";
      }
      showToast("Call request sent. Live audio is not integrated.", "warning");

      if (clientCallPollInterval) clearInterval(clientCallPollInterval);
      clientCallPollInterval = setInterval(async () => {
        try {
          const r = await fetch("/api/call/status");
          const d = await r.json();
          if (d.active && d.call && d.call.call_id === clientCallId) {
            if (d.call.status === "connected") {
              document.getElementById("snCallStatusText").textContent = "REQUEST ACCEPTED — AUDIO NOT CONNECTED";
            } else if (d.call.status === "declined" || d.call.status === "ended") {
              stopClientCallRequest("Support request closed.");
            }
          } else {
            stopClientCallRequest("Support request closed.");
          }
        } catch(e) {}
      }, 2000);
    }
  } catch (e) {
    showToast("Could not send the support request. Please try again.", "error");
  }
}

async function loadMyComplaints() {
  const tbody = document.getElementById("myComplaintsTableBody");
  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Loading complaints...</td></tr>`;

  try {
    const res = await fetch("/api/complaints/my-complaints");
    const data = await res.json();
    
    if (res.status === 401) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 36px;">
            <div style="font-weight: 800; color: var(--text-heading); margin-bottom: 8px;">Please Sign In to View Your Complaints History</div>
            <a href="/login" class="pill-tab active" style="text-decoration: none; display: inline-flex; align-items: center; gap: 8px; padding: 8px 24px;">
              <i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In / Register
            </a>
          </td>
        </tr>
      `;
      return;
    }

    const list = data.complaints || [];
    if (data.user_email) window.supportNovaCustomerEmail = data.user_email;
    const badge = document.getElementById("myComplaintsBadge");
    if (badge) badge.innerText = list.length;

    if (list.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 36px; color: var(--text-muted);">
            <i class="fa-solid fa-folder-open" style="font-size: 2rem; color: var(--primary); margin-bottom: 8px;"></i>
            <div>No complaints submitted under this account yet.</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = list.map(c => `
      <tr>
        <td><strong style="font-family: 'JetBrains Mono', monospace; color: var(--cream, #eef0d0);">${c.complaint_id}</strong></td>
        <td style="font-weight: 700; color: var(--text-heading);">${c.product_or_service || 'Hardware'}</td>
        <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.complaint_title}</td>
        <td>
          <span class="badge ${c.status === 'Resolved' ? 'badge-success' : (c.status === 'Escalated' ? 'badge-danger' : 'badge-primary')}">
            ${c.status || 'Under Review'}
          </span>
        </td>
        <td><span class="badge ${c.priority === 'P0' || c.priority === 'P1' ? 'badge-danger' : 'badge-warning'}">${c.priority || 'P2'}</span></td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${c.created_at || '-'}</td>
        <td>
          <button class="pill-tab" style="padding: 4px 12px; font-size: 0.78rem;" onclick="quickTrackTicket('${c.complaint_id}')">
            <i class="fa-solid fa-eye"></i> Track
          </button>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #e11d48; padding: 20px;">Error loading complaints: ${err}</td></tr>`;
  }
}

function quickTrackTicket(id) {
  switchPortalTab("track");
  window.supportNovaTrackTicket?.(id, window.supportNovaCustomerEmail || "");
}

async function handleComplaintSubmit(e) {
  e.preventDefault();
  const form = document.getElementById("complaintForm");
  const submitBtn = document.getElementById("submitFormBtn");
  const formData = new FormData(form);
  const evidenceImage = document.getElementById("complaintEvidenceImage");
  const evidenceConsent = document.getElementById("evidenceProcessingConsent");
  if (evidenceImage?.files?.length && !evidenceConsent?.checked) {
    evidenceConsent?.focus();
    showToast("Please consent to processing the attached photo, or remove it to continue.", "warning");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting to Official Support Operations...';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);
    const res = await fetch("/api/complaints/submit", {
      method: "POST",
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const data = await res.json();

    if (res.ok && data.success) {
      document.getElementById("registeredComplaintId").innerText = data.complaint_id;
      document.getElementById("submissionSuccessBox").style.display = "block";
      form.reset();
      document.getElementById("selectedProductBadge").style.display = "none";
      const visionBox = document.getElementById("visionAnalysisBox");
      if (visionBox) { visionBox.style.display = "none"; visionBox.textContent = ""; }
      const visionStatus = document.getElementById("visionUploadStatus");
      if (visionStatus) visionStatus.textContent = "Optional; maximum 10 MB. The original photo is not retained.";
      const removeImageButton = document.getElementById("removeEvidenceImage");
      if (removeImageButton) removeImageButton.style.display = "none";
      updateEvidenceConsent();
      document.getElementById("aiPreCheckBox").style.display = "none";
      
      document.querySelectorAll(".step-item").forEach(s => s.classList.add("active"));
      
      checkCustomerAuthState();
      showToast(`Complaint ${data.complaint_id} submitted successfully!`, "success");
    } else {
      showToast("Submission Error: " + (data.detail || "Unable to submit complaint."), "danger");
    }
  } catch (err) {
    showToast("Network or Server error: " + err, "danger");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane" style="margin-right: 8px;"></i> Submit Official Complaint to Support Operations';
  }
}

function copyAndTrack() {
  const id = document.getElementById("registeredComplaintId").innerText;
  const complaintEmail = document.getElementById("formCustomerEmail")?.value.trim();
  switchPortalTab("track");
  window.supportNovaTrackTicket?.(id, complaintEmail || "");
}

/* ==============================================================================
 * PRIORITY 5: AUTOMATIC SCROLL & ENTRANCE ANIMATION CONTROLLER
 * ============================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  // 1. Scroll Progress Bar Fill
  const bar = document.getElementById("scrollProgressBar");
  window.addEventListener("scroll", () => {
    if (!bar) return;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    if (total > 0) {
      const pct = (window.scrollY / total) * 100;
      bar.style.width = `${pct}%`;
    }
  }, { passive: true });

  // 2. IntersectionObserver for Scroll Reveals
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    document.querySelectorAll(".reveal-on-scroll").forEach(el => observer.observe(el));
  } else {
    document.querySelectorAll(".reveal-on-scroll").forEach(el => el.classList.add("revealed"));
  }
});

// Helper for Counting Up Numbers
function animateCountUp(elementId, endValue, duration = 800) {
  const el = document.getElementById(elementId);
  if (!el) return;
  let start = 0;
  const startTime = performance.now();
  
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (endValue - start) * easeOut);
    el.textContent = current;
    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.textContent = endValue;
    }
  }
  requestAnimationFrame(update);
}

