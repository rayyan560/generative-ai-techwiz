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
  toast.style.background = type === "danger" ? "#e11d48" : (type === "success" ? "#10b981" : (type === "warning" ? "#f59e0b" : "var(--cream, #eef0d0)"));
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
  toast.innerHTML = `<i class="fa-solid ${type === 'danger' ? 'fa-triangle-exclamation' : (type === 'success' ? 'fa-circle-check' : 'fa-circle-info')}"></i> <span>${message}</span>`;
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
  openCustomerGoogleModal();
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
  triggerAiPreCheck();
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
    triggerAiPreCheck();
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
      triggerAiPreCheck();
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
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];

  const dropText = document.getElementById("dropzoneText");
  const scanLine = document.getElementById("visionScanLine");
  if (scanLine) scanLine.style.display = "block";

  const statusStages = [
    "Multimodal AI scanning optical defect patterns...",
    "Verifying hardware fracture signatures...",
    "Matching warranty policy and OCR serial..."
  ];
  let stageIdx = 0;
  dropText.innerHTML = `<span style="color: var(--cream);"><i class="fa-solid fa-spinner fa-spin"></i> ${statusStages[0]}</span>`;
  const stageTimer = setInterval(() => {
    stageIdx = (stageIdx + 1) % statusStages.length;
    dropText.innerHTML = `<span style="color: var(--cream);"><i class="fa-solid fa-spinner fa-spin"></i> ${statusStages[stageIdx]}</span>`;
  }, 1200);

  const formData = new FormData();
  formData.append("file", file);
  formData.append("complaint_text", document.getElementById("complaintDescriptionInput").value);

  try {
    const res = await fetch("/api/vision/inspect", { method: "POST", body: formData });
    const data = await res.json();
    clearInterval(stageTimer);
    if (scanLine) scanLine.style.display = "none";

    dropText.innerHTML = `<span style="color: #10b981;"><i class="fa-solid fa-file-circle-check"></i> Image Analyzed: ${file.name}</span>`;

    const box = document.getElementById("visionAnalysisBox");
    box.style.display = "block";
    box.style.opacity = "0";
    box.style.transform = "translateY(8px)";
    box.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    setTimeout(() => {
      box.style.opacity = "1";
      box.style.transform = "translateY(0)";
    }, 50);

    document.getElementById("visionDefectType").innerText = data.defect_type;
    document.getElementById("visionConfidence").innerText = `${data.confidence_score}%`;
    document.getElementById("visionSerial").innerText = data.ocr_extracted_serial;
    document.getElementById("visionWarrantyImpact").innerText = data.warranty_policy_impact;

    const badge = document.getElementById("visionSeverityBadge");
    badge.innerText = data.severity;
    badge.className = `badge ${data.safety_hazard ? 'badge-danger' : 'badge-primary'}`;
  } catch (e) {
    clearInterval(stageTimer);
    if (scanLine) scanLine.style.display = "none";
    console.error("Error running vision analysis:", e);
  }
}

// -------------------------------------------------------------
// 3. ⚡ LIVE AI SLA & ELIGIBILITY PRE-CHECK ESTIMATOR
// -------------------------------------------------------------
let preCheckTimer = null;
function triggerAiPreCheck() {
  clearTimeout(preCheckTimer);
  preCheckTimer = setTimeout(async () => {
    const title = document.getElementById("complaintTitleInput").value;
    const desc = document.getElementById("complaintDescriptionInput").value;
    const tier = document.getElementById("customerTierSelect").value;

    if (!title && !desc) return;

    const formData = new FormData();
    formData.append("complaint_title", title || "Hardware Issue");
    formData.append("complaint_description", desc || "Support request");
    formData.append("customer_type", tier);

    try {
      const res = await fetch("/api/complaints/pre-check", { method: "POST", body: formData });
      const data = await res.json();

      const box = document.getElementById("aiPreCheckBox");
      box.style.display = "block";

      document.getElementById("preCheckCategoryBadge").innerText = `${data.estimated_category} (${data.estimated_priority})`;
      document.getElementById("preCheckSla").innerText = data.estimated_sla;
      document.getElementById("preCheckRefund").innerText = data.refund_eligibility_preview ? "Eligible (100% Policy Match)" : "Inspection Required";
      
      const sent = data.sentiment || {};
      document.getElementById("preCheckFrustration").innerText = `${sent.frustration_score || 50}% (${sent.emotion_state || 'Standard'})`;

    } catch (e) {
      console.error("Error running AI pre-check:", e);
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
      "sub": "اپنی شکایت درج کروائیں، تصویری ثبوت اپ لوڈ کریں یا آواز کے ذریعے شکایت ریکارڈ کروائیں۔"
    },
    "ar": {
      "title": "مركز خدمة العملاء وحل النزاعات والضمان",
      "sub": "قدم شكواك الرسمية، وقم بتحميل الأدلة المصورة للفحص الذكي الفوري."
    },
    "es": {
      "title": "Centro de Resolución de Garantías y Reclamaciones",
      "sub": "Envíe su queja oficial, cargue fotos para inspección visual por IA o dicte por voz."
    },
    "en": {
      "title": "Customer Complaint & Warranty Resolution Center",
      "sub": "Submit hardware grievances, upload photo evidence for instant AI defect analysis, or dictate issues via voice."
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

  [submitBtn, chatBtn, myComplaintsBtn, trackBtn].forEach(b => b && b.classList.remove("active"));
  [submitSec, chatSec, myComplaintsSec, trackSec].forEach(s => s && (s.style.display = "none"));

  if (tab === "submit") {
    submitBtn && submitBtn.classList.add("active");
    submitSec && (submitSec.style.display = "block");
  } else if (tab === "chat") {
    chatBtn && chatBtn.classList.add("active");
    chatSec && (chatSec.style.display = "block");
    loadCustChatMessages();
  } else if (tab === "my-complaints") {
    myComplaintsBtn && myComplaintsBtn.classList.add("active");
    myComplaintsSec && (myComplaintsSec.style.display = "block");
    loadMyComplaints();
  } else {
    trackBtn && trackBtn.classList.add("active");
    trackSec && (trackSec.style.display = "block");
  }
}

let custChatPollTimer = null;

async function loadCustChatMessages() {
  const box = document.getElementById("custChatMsgBox");
  if (!box) return;
  try {
    const res = await fetch("/api/chat/live/messages?client_id=USR-CUSTOMER");
    const data = await res.json();
    const msgs = data.messages || [];
    renderCustChatBubbles(msgs);
    if (custChatPollTimer) clearInterval(custChatPollTimer);
    custChatPollTimer = setInterval(async () => {
      try {
        const r = await fetch("/api/chat/live/messages?client_id=USR-CUSTOMER");
        const d = await r.json();
        renderCustChatBubbles(d.messages || []);
      } catch (e) {}
    }, 3500);
  } catch (e) {}
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
let clientCallTimerInterval = null;
let clientCallPollInterval = null;
let clientMediaStream = null;

async function startClientVoiceCall() {
  try {
    const res = await fetch("/api/call/initiate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: "USR-CUSTOMER", client_name: "Valued Customer" })
    });
    const data = await res.json();
    if (data.status === "unavailable") {
      showToast("⚠️ OWNER IS NOT AVAILABLE: No support officers are currently online", "error");
    } else if (data.status === "ringing") {
      clientCallId = data.call_id;
      const modal = document.getElementById("snVoiceCallBackdrop");
      if (modal) {
        document.getElementById("snCallName").textContent = data.target_staff ? data.target_staff.name : "Rayyan Ahmed Khan";
        document.getElementById("snCallSub").textContent = data.target_staff ? data.target_staff.role : "Super Admin & CEO";
        document.getElementById("snCallStatusText").textContent = "CALLING...";
        document.getElementById("snCallStatusText").style.color = "#25d366";
        modal.style.display = "flex";
      }
      showToast(`📞 Outgoing Voice Call placed to ${data.target_staff ? data.target_staff.name : "Support Team"}...`, "info");
      
      try {
        clientMediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch(e) {}

      if (clientCallPollInterval) clearInterval(clientCallPollInterval);
      clientCallPollInterval = setInterval(async () => {
        try {
          const r = await fetch("/api/call/status");
          const d = await r.json();
          if (d.active && d.call) {
            if (d.call.status === "connected") {
              document.getElementById("snCallStatusText").textContent = "CONNECTED (00:00)";
              if (!clientCallTimerInterval) {
                let sec = 0;
                clientCallTimerInterval = setInterval(() => {
                  sec++;
                  const m = String(Math.floor(sec / 60)).padStart(2, "0");
                  const s = String(sec % 60).padStart(2, "0");
                  document.getElementById("snCallStatusText").textContent = `CONNECTED (${m}:${s})`;
                }, 1000);
              }
            } else if (d.call.status === "declined" || d.call.status === "ended") {
              endCurrentCall();
            }
          } else {
            endCurrentCall();
          }
        } catch(e) {}
      }, 2000);
    }
  } catch (e) {
    showToast("Unable to connect call", "error");
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
  document.getElementById("trackInput").value = id;
  switchPortalTab("track");
  trackTicket();
}

async function handleComplaintSubmit(e) {
  e.preventDefault();
  const form = document.getElementById("complaintForm");
  const submitBtn = document.getElementById("submitFormBtn");
  const formData = new FormData(form);

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
      document.getElementById("visionAnalysisBox").style.display = "none";
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
  document.getElementById("trackInput").value = id;
  switchPortalTab("track");
  trackTicket();
}

async function trackTicket() {
  const input = document.getElementById("trackInput").value.trim();
  if (!input) {
    showToast("Please enter a valid Ticket Reference ID (e.g. CMP-00001)", "warning");
    return;
  }

  try {
    const res = await fetch(`/api/complaints/track/${input}`);
    const data = await res.json();

    if (!res.ok) {
      showToast(data.detail || "Ticket Reference ID not found.", "danger");
      return;
    }

    const box = document.getElementById("trackResultBox");
    box.style.display = "block";

    document.getElementById("trackTitle").innerText = data.complaint_title;
    document.getElementById("trackSub").innerText = `Ticket Ref: ${data.complaint_id} | Product/Service: ${data.product_or_service || 'Standard Order'}`;
    document.getElementById("trackTimeSubmitted").innerText = `Received on: ${data.submitted_at}`;
    document.getElementById("trackAssignedDept").innerText = data.assigned_department;
    document.getElementById("trackCustomerMessage").innerText = data.official_update;

    const badge = document.getElementById("trackStatusBadge");
    badge.innerText = data.status;
    badge.className = `badge ${data.status === 'Resolved' ? 'badge-success' : 'badge-primary'}`;

    const step3 = document.getElementById("timelineStep3");
    if (data.status === 'Resolved') {
      step3.className = "timeline-icon completed";
      step3.innerHTML = '<i class="fa-solid fa-check"></i>';
    } else {
      step3.className = "timeline-icon active-pulse";
      step3.innerHTML = '<i class="fa-solid fa-clock"></i>';
    }

  } catch (e) {
    console.error("Error tracking complaint:", e);
    showToast("Error tracking complaint: " + e, "danger");
  }
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

