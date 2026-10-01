(function () {
  'use strict';



  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     RUNTIME STATE
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  let ws            = null;
  let open          = false;
  let mode          = 'customer';
  let retries       = 0;
  let voiceOn       = false;
  let recog         = null;
  let tts           = window.speechSynthesis || null;
  let ttsActive     = false;
  let soundOn       = true;
  let locked        = false;
  let audioCtx      = null;
  const MAX_RETRY   = 5;

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     WEB AUDIO SCI-FI SYNTHESIZER
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

  let liveMode      = false;
  let liveConvId    = null;
  let livePollTimer = null;
  function playSciFiSound(type) {
    if (!soundOn) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      if (type === 'open') {
        // Futuristic Uplifting Dual-Chirp
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc.start(now);
        osc.stop(now + 0.18);
      } else if (type === 'send') {
        // Quantum Laser Transmit Ping
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(980, now);
        osc.frequency.exponentialRampToValueAtTime(320, now + 0.15);
        gain.gain.setValueAtTime(0.07, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
      } else if (type === 'recv') {
        // Holographic Data Receive Beep
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now);
        osc.frequency.setValueAtTime(880, now + 0.08);
        gain.gain.setValueAtTime(0.09, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
        osc.start(now);
        osc.stop(now + 0.22);
      } else if (type === 'click') {
        // High-Tech Micro Tick
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1400, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.05);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
      }
    } catch (e) {
      // AudioContext policy gracefully handled
    }
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     ROUTE & CONTEXT MODE DETECTION
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function detectMode() {
    const p = location.pathname;
    return (p.startsWith('/admin') || p.startsWith('/communication') ||
            p.startsWith('/refunds') || p.startsWith('/analytics') ||
            p.startsWith('/knowledge') || p.startsWith('/rules'))
      ? 'admin' : 'customer';
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     BRAND THEME METADATA
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function theme(isAdmin) {
    return isAdmin ? {
      name     : 'NovaOps AI Co-Pilot',
      tagline  : 'Quantum Triage Intelligence Core',
      modeTag  : 'ADMIN HUD // LIVE TRIAGE',
      role     : 'ResponseX AI Autonomous Co-Pilot',
      icon     : 'fa-shield-halved',
      bootText : 'NOVAOPS QUANTUM MATRIX ONLINE',
      bootSub  : 'Neural core synchronized. Query live queues, policy matrices, or SLA risks.'
    } : {
      name     : 'SupportNova Intelligent Assistant',
      tagline  : 'Autonomous Customer Intelligence',
      modeTag  : 'NOVA CARE // 24/7 ONLINE',
      role     : 'Autonomous Service & Warranty AI',
      icon     : 'fa-robot',
      bootText : 'SUPPORTNOVA AI SYSTEM READY',
      bootSub  : 'Greetings! I am SupportNova AI. How may I assist with your warranty, refund, or claims today?'
    };
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     NOVA MULTI-RING ARC-REACTOR 3.0 SVG CORE
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function jarvisReactorSVG(size, uid) {
    return `
    <svg class="sn-jarvis-svg" width="${size}" height="${size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="snArcCore${uid}" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="25%" stop-color="#eef0d0"/>
          <stop offset="60%" stop-color="#eef0d0"/>
          <stop offset="100%" stop-color="#f59e0b"/>
        </radialGradient>
        <filter id="snGlowFX${uid}" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="b1"/>
          <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b2"/>
          <feMerge>
            <feMergeNode in="b2"/>
            <feMergeNode in="b1"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- Outer Cardinal HUD Coordinate Brackets -->
      <g stroke="rgba(238, 240, 208, 0.85)" stroke-width="1.8" fill="none">
        <line x1="60" y1="2" x2="60" y2="9"/>
        <line x1="60" y1="111" x2="60" y2="118"/>
        <line x1="2" y1="60" x2="9" y2="60"/>
        <line x1="111" y1="60" x2="118" y2="60"/>
      </g>

      <!-- Outer Segmented Quantum Gyro Ring 1 -->
      <circle class="sn-svg-ring-1" cx="60" cy="60" r="50" fill="none" stroke="rgba(238, 240, 208, 0.75)" stroke-width="2" stroke-dasharray="20 8 36 8" filter="url(#snGlowFX${uid})"/>

      <!-- Counter-Rotating Neon Dashed Ring 2 -->
      <circle class="sn-svg-ring-2" cx="60" cy="60" r="41" fill="none" stroke="rgba(245, 158, 11, 0.85)" stroke-width="2" stroke-dasharray="8 6 18 6"/>

      <!-- High-Speed Micro-Orbit Dotted Ring 3 -->
      <circle class="sn-svg-ring-3" cx="60" cy="60" r="32" fill="none" stroke="rgba(238, 240, 208, 0.95)" stroke-width="1.5" stroke-dasharray="3 5"/>

      <!-- Central Rotating Hex-Shield Iris -->
      <polygon class="sn-svg-hex" points="60,38 77,47 77,71 60,82 43,71 43,47" fill="none" stroke="rgba(255, 255, 255, 0.85)" stroke-width="1.2"/>

      <!-- Glowing Arc Reactor Plasma Core Center -->
      <circle class="sn-svg-core" cx="60" cy="60" r="14" fill="url(#snArcCore${uid})" filter="url(#snGlowFX${uid})"/>
      <circle cx="60" cy="60" r="5.5" fill="#ffffff" opacity="0.95"/>
    </svg>`;
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     MARKDOWN & RICH RESPONSE PARSER
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function md(text) {
    if (!text) return '';
    let decoded = text;
    if (decoded.includes('&lt;') || decoded.includes('&gt;')) {
      const txt = document.createElement('textarea');
      txt.innerHTML = decoded;
      decoded = txt.value;
    }
    let t = decoded
      .replace(/\*\*(.+?)\*\*/g,'<strong class="sn-strong">$1</strong>')
      .replace(/\*([^*\n]+?)\*/g,'<em class="sn-em">$1</em>')
      .replace(/`([^`]+?)`/g,'<code class="sn-code">$1</code>');
    const lines = t.split('\n');
    let out='', inList=false;
    lines.forEach(ln => {
      const li = ln.match(/^[\s]*[\*\-•] (.+)/);
      const nm = ln.match(/^[\s]*\d+\. (.+)/);
      if (li || nm) {
        if (!inList) { out += '<ul class="sn-list">'; inList = true; }
        out += `<li><i class="fa-solid fa-angle-right sn-list-icon"></i> ${(li || nm)[1]}</li>`;
      } else {
        if (inList) { out += '</ul>'; inList = false; }
        const trimmed = (ln || '').trim();
        if (!trimmed) {
          out += '<br>';
        } else if (trimmed.startsWith('<')) {
          out += ln + '<br>';
        } else {
          out += `<span class="sn-line">${ln}</span><br>`;
        }
      }
    });
    if (inList) out += '</ul>';
    return out;
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     INJECT FUTURISTIC NOVA STYLESHEET
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function injectCSS() {
    const css = `
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SUPPORTNOVA HOLOGRAPHIC CHATBOT STYLESHEET (PRO GRADE SCI-FI HUD)
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

@keyframes waMsgIn {
  0%   { opacity: 0; transform: scale(0.88) translateY(10px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes waTickAppear {
  0%   { opacity: 0; transform: translateX(-6px); }
  100% { opacity: 1; transform: translateX(0); }
}
@keyframes waTypeDot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
  30%           { transform: translateY(-6px); opacity: 1; }
}

/* â”€â”€ 1. SIGNATURE GPU KEYFRAMES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
@keyframes snRotateCW    { from { transform: rotate(0deg); }   to { transform: rotate(360deg); } }
@keyframes snRotateCCW   { from { transform: rotate(0deg); }   to { transform: rotate(-360deg); } }

@keyframes snPulseAura {
  0%, 100% { opacity: 0.75; transform: scale(1); filter: drop-shadow(0 0 18px rgba(238, 240, 208, 0.6)); }
  50%      { opacity: 0.35; transform: scale(1.3); filter: drop-shadow(0 0 35px rgba(245, 158, 11, 0.8)); }
}

@keyframes snCoreBreath {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 12px rgba(238, 240, 208, 0.75)); }
  50%      { transform: scale(1.12); filter: drop-shadow(0 0 24px rgba(245, 158, 11, 0.95)) drop-shadow(0 0 40px rgba(238, 240, 208, 0.8)); }
}

@keyframes snCoreRapidPulse {
  0%, 100% { transform: scale(1) rotate(0deg); }
  50%      { transform: scale(1.2) rotate(180deg); filter: drop-shadow(0 0 28px #eef0d0) drop-shadow(0 0 45px #f59e0b); }
}

@keyframes snRadarSweep {
  0%   { top: 0%; opacity: 0.9; }
  50%  { opacity: 0.25; }
  100% { top: 100%; opacity: 0.9; }
}

@keyframes snWaveBar {
  0%, 100% { height: 4px; opacity: 0.5; }
  50%      { height: 28px; opacity: 1; }
}

@keyframes snShimmerSweep {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes snPanelEntrance {
  0%   { opacity: 0; transform: translateY(35px) scale(0.92); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes snPanelExit {
  0%   { opacity: 1; transform: translateY(0) scale(1); }
  100% { opacity: 0; transform: translateY(28px) scale(0.94); }
}

@keyframes snBeaconPulse {
  0%   { box-shadow: 0 0 0 0 rgba(238, 240, 208, 0.8); }
  70%  { box-shadow: 0 0 0 10px rgba(238, 240, 208, 0); }
  100% { box-shadow: 0 0 0 0 rgba(238, 240, 208, 0); }
}

/* â”€â”€ 2. FLOATING ARC REACTOR LAUNCHER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snLauncher {
  position: fixed !important;
  bottom: 24px !important;
  right: 24px !important;
  z-index: 999999 !important;
  width: 72px !important;
  height: 72px !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  user-select: none !important;
  border-radius: 50% !important;
  background: radial-gradient(circle at 35% 35%, rgba(238, 240, 208, 0.95), rgba(238, 240, 208, 0.95) 50%, rgba(15, 23, 42, 0.95) 100%) !important;
  box-shadow: 0 12px 40px rgba(238, 240, 208, 0.55), 0 0 25px rgba(238, 240, 208, 0.45) !important;
  border: 2px solid rgba(255, 255, 255, 0.8) !important;
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease !important;
}

#snLauncher:hover {
  transform: scale(1.14) translateY(-3px) !important;
  box-shadow: 0 18px 55px rgba(245, 158, 11, 0.75), 0 0 35px rgba(245, 158, 11, 0.6) !important;
}

#snLauncher:active {
  transform: scale(0.94) !important;
}

#snAura {
  position: absolute;
  inset: -16px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(238, 240, 208, 0.5) 0%, rgba(238, 240, 208, 0.25) 50%, transparent 72%);
  animation: snPulseAura 3s ease-in-out infinite;
  pointer-events: none;
}

#snHUD {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

#snHUD .sn-jarvis-svg {
  width: 64px;
  height: 64px;
}

#snHUD .sn-svg-ring-1 { transform-origin: 60px 60px; animation: snRotateCW 9s linear infinite; }
#snHUD .sn-svg-ring-2 { transform-origin: 60px 60px; animation: snRotateCCW 5.5s linear infinite; }
#snHUD .sn-svg-ring-3 { transform-origin: 60px 60px; animation: snRotateCW 3s linear infinite; }
#snHUD .sn-svg-hex    { transform-origin: 60px 60px; animation: snRotateCCW 12s linear infinite; }
#snHUD .sn-svg-core   { animation: snCoreBreath 2.6s ease-in-out infinite; }

#snHUD.processing .sn-svg-ring-1 { animation: snRotateCW 1.8s linear infinite !important; stroke: #eef0d0 !important; }
#snHUD.processing .sn-svg-ring-2 { animation: snRotateCCW 1.1s linear infinite !important; stroke: #f59e0b !important; }
#snHUD.processing .sn-svg-core   { animation: snCoreRapidPulse 0.75s ease-in-out infinite !important; }

#snBadge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: linear-gradient(135deg, #e11d48, #ff2a8d);
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 900;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ffffff;
  z-index: 10;
  box-shadow: 0 0 14px rgba(225, 29, 72, 0.9);
  animation: snBeaconPulse 2s infinite;
}

/* â”€â”€ 3. HOLOGRAPHIC TRANSPARENT CHAT TERMINAL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snWin {
  position: fixed !important;
  bottom: 106px !important;
  right: 24px !important;
  z-index: 999998 !important;
  width: 440px !important;
  height: 640px !important;
  max-width: calc(100vw - 32px) !important;
  max-height: calc(100vh - 128px) !important;
  border-radius: 28px !important;
  display: none;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif !important;
  background: rgba(18, 22, 20, 0.97) !important;
  backdrop-filter: blur(28px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(28px) saturate(160%) !important;
  border: 1px solid rgba(214, 217, 170, 0.45) !important;
  box-shadow: 
    0 30px 95px rgba(0, 0, 0, 0.85), 
    0 0 45px rgba(214, 217, 170, 0.22),
    inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

html[data-theme="dark"] #snWin {
  background: rgba(18, 22, 20, 0.97) !important;
  border: 1px solid rgba(214, 217, 170, 0.45) !important;
  box-shadow: 
    0 30px 95px rgba(0, 0, 0, 0.85), 
    0 0 45px rgba(214, 217, 170, 0.22), 
    inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
}

/* Holographic Cyber Matrix Grid Overlay */
#snHUDGrid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: 
    linear-gradient(rgba(238, 240, 208, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(238, 240, 208, 0.05) 1px, transparent 1px);
  background-size: 24px 24px;
  z-index: 0;
  opacity: 0.7;
}

/* Radar Laser Scanning Beam */
#snScan {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 25;
  pointer-events: none;
  background: linear-gradient(90deg, transparent 0%, #eef0d0 35%, #ffffff 50%, #f59e0b 65%, transparent 100%);
  box-shadow: 0 0 14px #eef0d0, 0 0 24px rgba(245, 158, 11, 0.6);
  animation: snRadarSweep 5.5s ease-in-out infinite;
}

/* â”€â”€ 4. HOLOGRAPHIC HEADER (NOVA HUD) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */

/* WhatsApp Live Chat Styles */
.sn-wa-toggle-bar {
  display: flex;
  gap: 0;
  background: rgba(255,255,255,0.12);
  border-radius: 9999px;
  border: 1px solid rgba(255,255,255,0.3);
  overflow: hidden;
  padding: 3px;
  flex-shrink: 0;
}
.sn-wa-tab {
  flex: 1;
  padding: 6px 12px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.3px;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  background: transparent;
  color: rgba(255,255,255,0.75);
  transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: 'Outfit', sans-serif;
}
.sn-wa-tab.active {
  background: rgba(255,255,255,0.95);
  color: #0f172a;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.sn-wa-tab.wa-active {
  background: linear-gradient(135deg, #25d366, #128c7e);
  color: #ffffff;
  box-shadow: 0 2px 14px rgba(37,211,102,0.45);
}

#snLiveChat {
  flex: 1;
  display: none;
  flex-direction: column;
  overflow: hidden;
}
#snLiveChat.active { display: flex; }

.sn-wa-header {
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(37,211,102,0.25) 0%, rgba(18,140,126,0.2) 100%);
  border-bottom: 1px solid rgba(37,211,102,0.3);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.sn-wa-officer-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #25d366;
  box-shadow: 0 0 10px rgba(37,211,102,0.5);
  flex-shrink: 0;
}
.sn-wa-officer-name {
  font-weight: 800;
  font-size: 0.88rem;
  color: #ffffff;
  text-shadow: 0 0 8px rgba(37,211,102,0.4);
}
.sn-wa-officer-role {
  font-size: 0.70rem;
  color: rgba(255,255,255,0.75);
  margin-top: 1px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.sn-wa-online-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #25d366;
  box-shadow: 0 0 8px #25d366;
  animation: snBeaconPulse 2s infinite;
  flex-shrink: 0;
}

#snWaMsgs {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(37,211,102,0.3) transparent;
  background: transparent;
}
#snWaMsgs::-webkit-scrollbar { width: 4px; }
#snWaMsgs::-webkit-scrollbar-thumb { background: rgba(37,211,102,0.35); border-radius: 4px; }

.sn-wa-msg-wrap { animation: waMsgIn 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards; }

.sn-wa-bubble-out {
  margin-left: auto;
  background: linear-gradient(135deg, rgba(238, 240, 208, 0.9) 0%, rgba(245, 158, 11, 0.9) 100%);
  color: #ffffff;
  border-radius: 16px 16px 3px 16px;
  padding: 9px 14px;
  max-width: 82%;
  font-size: 0.86rem;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 4px 14px rgba(238, 240, 208, 0.3);
}
.sn-wa-bubble-in {
  margin-right: auto;
  background: rgba(255,255,255,0.88);
  color: #0f172a;
  border-radius: 3px 16px 16px 16px;
  padding: 9px 14px;
  max-width: 82%;
  font-size: 0.86rem;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  backdrop-filter: blur(6px);
}
html[data-theme="dark"] .sn-wa-bubble-in {
  background: rgba(30,41,59,0.85);
  color: #f1f5f9;
}
.sn-wa-meta {
  font-size: 0.65rem;
  color: rgba(255,255,255,0.65);
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: flex-end;
}
.sn-wa-meta.in-meta {
  color: #94a3b8;
  justify-content: flex-start;
}
.sn-wa-ticks {
  color: #00a9ff;
  font-size: 0.70rem;
  animation: waTickAppear 0.4s ease;
}
.sn-wa-typing {
  display: none;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.sn-wa-typing.on { display: flex; }
.sn-wa-typing-bubble {
  background: rgba(255,255,255,0.82);
  border-radius: 3px 14px 14px 14px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07);
}
html[data-theme="dark"] .sn-wa-typing-bubble {
  background: rgba(30,41,59,0.8);
}
.sn-wa-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #25d366;
  animation: waTypeDot 1.2s ease-in-out infinite;
}
.sn-wa-dot:nth-child(2) { animation-delay: 0.2s; }
.sn-wa-dot:nth-child(3) { animation-delay: 0.4s; }
.sn-wa-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-top: 1px solid rgba(37,211,102,0.2);
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}
#snWaInput {
  flex: 1;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(37,211,102,0.4);
  border-radius: 22px;
  padding: 9px 16px;
  color: #0f172a;
  font-size: 0.86rem;
  font-family: inherit;
  outline: none;
  transition: all 0.25s ease;
}
html[data-theme="dark"] #snWaInput { color: #f1f5f9; background: rgba(30,41,59,0.3); }
#snWaInput:focus {
  border-color: #25d366;
  box-shadow: 0 0 0 3px rgba(37,211,102,0.2);
  background: rgba(255,255,255,0.3);
}
#snWaInput::placeholder { color: #94a3b8; }
#snWaSend {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg,#25d366,#128c7e);
  border: none;
  cursor: pointer;
  color: #ffffff;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(37,211,102,0.4);
  transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
#snWaSend:hover { transform: scale(1.1); box-shadow: 0 6px 18px rgba(37,211,102,0.6); }
.sn-wa-sys {
  text-align: center;
  font-size: 0.70rem;
  color: #94a3b8;
  background: rgba(255,255,255,0.18);
  border-radius: 9999px;
  padding: 3px 12px;
  width: fit-content;
  margin: 2px auto;
  backdrop-filter: blur(6px);
}
#snHeader {
  padding: 14px 18px !important;
  display: flex !important;
  align-items: center !important;
  gap: 12px !important;
  background: linear-gradient(135deg, rgba(238, 240, 208, 0.82) 0%, rgba(245, 158, 11, 0.78) 60%, rgba(245, 158, 11, 0.74) 100%) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  color: #ffffff !important;
  position: relative !important;
  flex-shrink: 0 !important;
  z-index: 5 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.35) !important;
  box-shadow: 0 4px 20px rgba(238, 240, 208, 0.3) !important;
}

#snHeader::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2.5px;
  background: linear-gradient(90deg, var(--cream, #eef0d0) 0%, #eef0d0 35%, #f59e0b 70%, #eef0d0 100%);
  background-size: 200% 100%;
  animation: snShimmerSweep 3s linear infinite;
}

.sn-avatar-wrap {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  border: 1px solid rgba(238, 240, 208, 0.5);
  box-shadow: 0 0 16px rgba(238, 240, 208, 0.3);
  overflow: hidden;
}

.sn-avatar-wrap .sn-jarvis-svg {
  width: 38px;
  height: 38px;
}

#snBotName {
  font-family: 'Outfit', 'Orbitron', sans-serif;
  font-size: 1.05rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.2px;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.2;
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.4);
}

.sn-mode-tag {
  font-family: 'JetBrains Mono', 'Orbitron', monospace;
  font-size: 0.60rem;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(238, 240, 208, 0.2);
  border: 1px solid rgba(238, 240, 208, 0.6);
  color: #eef0d0;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  text-shadow: 0 0 8px rgba(238, 240, 208, 0.8);
}

#snStatus {
  font-size: 0.74rem;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  font-weight: 500;
}

.sn-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #eef0d0;
  box-shadow: 0 0 10px #eef0d0;
  animation: snBeaconPulse 2s infinite;
  flex-shrink: 0;
}

.sn-hbtn {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #ffffff;
  cursor: pointer;
  border-radius: 10px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
}

.sn-hbtn:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px) scale(1.08);
  box-shadow: 0 0 14px #eef0d0;
}

/* â”€â”€ 5. ADMIN SHORTCUT / PORTAL LINK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snPortal {
  padding: 8px 14px;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
  flex-shrink: 0;
  z-index: 5;
}

html[data-theme="dark"] #snPortal {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 23, 42, 0.15);
}

.sn-portal-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(238, 240, 208, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: var(--cream, #eef0d0);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.25s ease;
}

.sn-portal-btn:hover {
  background: var(--cream, #eef0d0);
  color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 0 12px rgba(238, 240, 208, 0.5);
}

/* â”€â”€ 6. QUICK ACTION CHIPS (NEON GLASS PILLS) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snChips {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.25);
  display: flex;
  gap: 8px;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
  z-index: 5;
}
#snChips::-webkit-scrollbar { display: none; }

html[data-theme="dark"] #snChips {
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(15, 23, 42, 0.15);
}

.sn-chip {
  white-space: nowrap;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #f8fafc;
  font-size: 0.76rem;
  font-weight: 600;
  padding: 6px 13px;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: inherit;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

html[data-theme="dark"] .sn-chip {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #f8fafc;
}

.sn-chip:hover {
  background: rgba(5, 150, 105, 0.35);
  border-color: #34d399;
  color: #34d399;
  transform: translateY(-2px) scale(1.03);
  box-shadow: 0 6px 18px rgba(5, 150, 105, 0.4);
}

/* â”€â”€ 7. MESSAGES FEED â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snMsgs {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(238, 240, 208, 0.4) transparent;
  position: relative;
  z-index: 5;
  background: transparent !important;
}

#snMsgs::-webkit-scrollbar { width: 5px; }
#snMsgs::-webkit-scrollbar-thumb { background: rgba(238, 240, 208, 0.45); border-radius: 4px; }

.sn-wrap {
  animation: snPanelEntrance 0.32s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

/* User Bubble (Translucent Gradient Glass) */
.sn-user {
  background: linear-gradient(135deg, rgba(238, 240, 208, 0.90) 0%, rgba(245, 158, 11, 0.90) 100%);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #ffffff;
  border-radius: 18px 18px 4px 18px;
  padding: 11px 16px;
  font-size: 0.88rem;
  line-height: 1.55;
  max-width: 84%;
  margin-left: auto;
  box-shadow: 0 6px 20px rgba(238, 240, 208, 0.3), 0 0 15px rgba(245, 158, 11, 0.2);
  word-break: break-word;
  font-weight: 500;
}

/* Bot Response Bubble (Transparent Holographic Glass) */
.sn-bot {
  background: rgba(28, 34, 30, 0.96) !important;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(214, 217, 170, 0.38) !important;
  border-left: 4px solid #d4d9aa !important;
  color: #ffffff !important;
  border-radius: 4px 18px 18px 18px;
  padding: 14px 18px;
  font-size: 0.90rem;
  line-height: 1.65;
  max-width: 92%;
  position: relative;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.12);
  word-break: break-word;
}

.sn-bot, .sn-bot *, .sn-bot p, .sn-bot div, .sn-bot span, .sn-bot .sn-line {
  color: #f8fafc !important;
}

html[data-theme="dark"] .sn-bot {
  background: rgba(28, 34, 30, 0.96) !important;
  border: 1px solid rgba(214, 217, 170, 0.38) !important;
  border-left: 4px solid #d4d9aa !important;
  color: #ffffff !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.12);
}

.sn-bot.speaking {
  border-left-color: #f59e0b !important;
  box-shadow: 0 0 25px rgba(245, 158, 11, 0.5) !important;
}

.sn-strong, .sn-bot strong, .sn-bot b {
  color: #ffffff !important;
  font-weight: 800 !important;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.25) !important;
}
html[data-theme="dark"] .sn-strong { color: #ffffff !important; }

.sn-em { color: #d4d9aa !important; font-style: italic; }
.sn-list { margin: 8px 0 8px 10px !important; padding: 0 !important; list-style: none !important; }
.sn-list li {
  margin-bottom: 6px !important;
  display: flex !important;
  align-items: flex-start !important;
  gap: 8px !important;
  color: #f8fafc !important;
  font-weight: 500 !important;
  font-size: 0.90rem !important;
  line-height: 1.55 !important;
}
.sn-list-icon { color: #d4d9aa !important; font-size: 0.82rem !important; margin-top: 3px !important; flex-shrink: 0 !important; }
.sn-code {
  background: rgba(15, 23, 42, 0.8) !important;
  border: 1px solid rgba(214, 217, 170, 0.4) !important;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
  color: #d4d9aa !important;
  font-weight: 700;
}

.sn-time {
  font-size: 0.70rem;
  color: #94a3b8 !important;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}
.sn-time.r { justify-content: flex-end; }

.sn-sys {
  text-align: center;
  font-size: 0.73rem;
  color: #64748b;
  padding: 4px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.35);
  margin: 4px auto;
  width: fit-content;
}

html[data-theme="dark"] .sn-sys {
  background: rgba(15, 23, 42, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #94a3b8;
}

.sn-speak-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  transition: all 0.25s ease;
}
.sn-speak-btn:hover { color: #eef0d0; transform: scale(1.18); }

/* â”€â”€ 8. NEURAL SCANNER (TYPING INDICATOR) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snTyping {
  display: none;
  flex-direction: column;
  gap: 6px;
  z-index: 5;
}

.sn-typing-bubble {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.30);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-left: 3.5px solid #eef0d0;
  padding: 11px 16px;
  border-radius: 4px 16px 16px 16px;
  width: fit-content;
  box-shadow: 0 0 20px rgba(238, 240, 208, 0.25);
}

html[data-theme="dark"] .sn-typing-bubble {
  background: rgba(30, 41, 59, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.sn-quantum-nodes {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sn-qnode {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #eef0d0;
  box-shadow: 0 0 10px #eef0d0;
  animation: snCoreRapidPulse 1.2s ease-in-out infinite;
}
.sn-qnode:nth-child(2) { animation-delay: 0.2s; background: #eef0d0; box-shadow: 0 0 10px #eef0d0; }
.sn-qnode:nth-child(3) { animation-delay: 0.4s; background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }

.sn-tlabel {
  font-family: 'Outfit', sans-serif;
  font-size: 0.74rem;
  font-weight: 700;
  color: #eef0d0;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8px rgba(238, 240, 208, 0.5);
}

/* â”€â”€ 9. BOOT SCREEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snBoot {
  text-align: center;
  padding: 24px 16px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 5;
}

.sn-boot-reactor {
  width: 76px;
  height: 76px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 0 20px rgba(238, 240, 208, 0.5));
}

.sn-boot-reactor .sn-jarvis-svg {
  width: 100%;
  height: 100%;
}

.sn-boot-label {
  font-family: 'Outfit', 'Orbitron', sans-serif;
  font-size: 0.90rem;
  letter-spacing: 0.8px;
  color: #ffffff;
  font-weight: 800;
  text-shadow: 0 0 10px rgba(238, 240, 208, 0.3);
}
html[data-theme="dark"] .sn-boot-label { color: #ffffff; }

.sn-boot-sub {
  font-size: 0.78rem;
  color: #cbd5e1;
  max-width: 290px;
  line-height: 1.5;
}

.sn-boot-bar {
  width: 65%;
  height: 2.5px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--cream, #eef0d0) 0%, #eef0d0 35%, #f59e0b 70%, #eef0d0 100%);
  background-size: 200% 100%;
  animation: snShimmerSweep 3s linear infinite;
  box-shadow: 0 0 12px rgba(238, 240, 208, 0.6);
}

/* â”€â”€ 10. VOICE HARMONIC HUD OVERLAY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snVoice {
  display: none;
  position: absolute;
  inset: 0;
  background: rgba(9, 13, 22, 0.88);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  z-index: 50;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

#snVoice.on { display: flex; }

.sn-vbars {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 36px;
}

.sn-vbar {
  width: 4px;
  background: linear-gradient(180deg, #eef0d0, #f59e0b);
  border-radius: 2px;
  box-shadow: 0 0 10px #eef0d0;
  animation: snWaveBar 0.65s ease-in-out infinite;
}
.sn-vbar:nth-child(1) { animation-delay: 0.00s; height: 8px; }
.sn-vbar:nth-child(2) { animation-delay: 0.12s; height: 16px; }
.sn-vbar:nth-child(3) { animation-delay: 0.24s; height: 28px; }
.sn-vbar:nth-child(4) { animation-delay: 0.36s; height: 18px; }
.sn-vbar:nth-child(5) { animation-delay: 0.48s; height: 32px; }
.sn-vbar:nth-child(6) { animation-delay: 0.20s; height: 22px; }
.sn-vbar:nth-child(7) { animation-delay: 0.32s; height: 14px; }
.sn-vbar:nth-child(8) { animation-delay: 0.44s; height: 26px; }
.sn-vbar:nth-child(9) { animation-delay: 0.16s; height: 10px; }

#snVoicePulse {
  width: 90px;
  height: 90px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

#snVoicePulse .sn-jarvis-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 28px #eef0d0);
}

#snVoiceLabel {
  font-family: 'Outfit', 'Orbitron', sans-serif;
  color: #ffffff;
  font-weight: 900;
  font-size: 1.1rem;
  letter-spacing: 1.5px;
  text-shadow: 0 0 16px #eef0d0;
}

#snVoiceSub {
  color: #94a3b8;
  font-size: 0.82rem;
}

.sn-vstop {
  background: rgba(225, 29, 72, 0.25);
  border: 1px solid #e11d48;
  color: #fda4af;
  padding: 10px 26px;
  border-radius: 12px;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.8px;
  transition: all 0.25s ease;
  box-shadow: 0 0 18px rgba(225, 29, 72, 0.5);
}

.sn-vstop:hover {
  background: #e11d48;
  color: #ffffff;
  transform: scale(1.05);
}

/* â”€â”€ 11. INPUT DOCK & ACTION BUTTONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#snInputArea {
  padding: 12px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.35);
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  flex-shrink: 0;
  position: relative;
  z-index: 5;
}

#snInputArea {
  padding: 12px 14px;
  border-top: 1px solid rgba(214, 217, 170, 0.35) !important;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: rgba(18, 22, 20, 0.98) !important;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  flex-shrink: 0;
  position: relative;
  z-index: 5;
}

html[data-theme="dark"] #snInputArea {
  border-top: 1px solid rgba(214, 217, 170, 0.35) !important;
  background: rgba(18, 22, 20, 0.98) !important;
}

#snInput {
  flex: 1;
  background: rgba(30, 36, 33, 0.96) !important;
  border: 1px solid rgba(214, 217, 170, 0.40) !important;
  border-radius: 14px;
  padding: 11px 16px;
  color: #ffffff !important;
  font-size: 0.90rem;
  font-family: inherit;
  resize: none;
  outline: none;
  line-height: 1.45;
  max-height: 96px;
  overflow-y: auto;
  transition: all 0.25s ease;
  scrollbar-width: none;
}

html[data-theme="dark"] #snInput {
  background: rgba(30, 36, 33, 0.96) !important;
  border: 1px solid rgba(214, 217, 170, 0.40) !important;
  color: #ffffff !important;
}

#snInput:focus {
  border-color: #d4d9aa !important;
  background: rgba(36, 44, 40, 0.98) !important;
  box-shadow: 0 0 0 3px rgba(214, 217, 170, 0.25), 0 0 16px rgba(214, 217, 170, 0.25) !important;
}

html[data-theme="dark"] #snInput:focus {
  background: rgba(36, 44, 40, 0.98) !important;
}

#snInput::placeholder {
  color: rgba(226, 232, 240, 0.72) !important;
}

#snInput::-webkit-scrollbar { display: none; }

.sn-ibtn {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  border: 1px solid rgba(214, 217, 170, 0.35) !important;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.12) !important;
  color: #f8fafc !important;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

html[data-theme="dark"] .sn-ibtn {
  background: rgba(255, 255, 255, 0.12) !important;
  border: 1px solid rgba(214, 217, 170, 0.35) !important;
  color: #f8fafc !important;
}

.sn-ibtn:hover {
  background: rgba(214, 217, 170, 0.25) !important;
  color: #ffffff !important;
  transform: translateY(-2px);
  border-color: #d4d9aa !important;
  box-shadow: 0 0 14px rgba(214, 217, 170, 0.4) !important;
}

#snSend {
  background: #d4d9aa !important;
  color: #101010 !important;
  font-weight: 800 !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(214, 217, 170, 0.4), 0 0 15px rgba(214, 217, 170, 0.3) !important;
}

#snSend:hover {
  background: #e2e6bf !important;
  transform: scale(1.08) translateY(-2px) !important;
  box-shadow: 0 6px 24px rgba(214, 217, 170, 0.6) !important;
}

#snSend:disabled {
  opacity: 0.4 !important;
  transform: none !important;
  cursor: default !important;
  box-shadow: none !important;
}

#snMic.rec {
  background: rgba(225, 29, 72, 0.35) !important;
  border-color: #e11d48 !important;
  color: #fda4af !important;
  box-shadow: 0 0 20px rgba(225, 29, 72, 0.7) !important;
  animation: snBeaconPulse 1.5s infinite !important;
}

#snTts.on {
  color: #eef0d0 !important;
  border-color: #eef0d0 !important;
  background: rgba(238, 240, 208, 0.18) !important;
  box-shadow: 0 0 12px rgba(238, 240, 208, 0.35) !important;
}

/* â”€â”€ 12. REDUCED MOTION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
@media (prefers-reduced-motion: reduce) {
  #snHUD .sn-svg-ring-1,
  #snHUD .sn-svg-ring-2,
  #snHUD .sn-svg-ring-3,
  #snHUD .sn-svg-hex,
  #snHUD .sn-svg-core,
  #snScan,
  #snAura,
  .sn-vbar {
    animation: none !important;
  }
}
    `;

    let el = document.getElementById('snChatCSS');
    if (!el) {
      el = document.createElement('style');
      el.id = 'snChatCSS';
      document.head.appendChild(el);
    }
    el.textContent = css;
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     BUILD HTML SHELL (NOVA HUD & PANELS)
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function buildHTML(T, isAdmin) {
    const existing = document.getElementById('snRoot');
    if (existing) existing.remove();

    const adminChips = `
      <button class="sn-chip" onclick="SNC.q('Show all P0 critical and safety hazard complaints')"><i class="fa-solid fa-triangle-exclamation" style="color:#e11d48;"></i> P0 Critical</button>
      <button class="sn-chip" onclick="SNC.q('Give me live complaint statistics and trend overview')"><i class="fa-solid fa-chart-pie" style="color:#eef0d0;"></i> Live Stats</button>
      <button class="sn-chip" onclick="SNC.q('Which complaints need urgent escalation right now?')"><i class="fa-solid fa-bolt" style="color:#d97706;"></i> Escalate</button>
      <button class="sn-chip" onclick="SNC.q('Filter all Safety Hazard category complaints')"><i class="fa-solid fa-fire-flame-curved" style="color:#f59e0b;"></i> Safety</button>
      <button class="sn-chip" onclick="SNC.q('Which SLA deadlines are at risk or already breached?')"><i class="fa-solid fa-clock-rotate-left" style="color:#eef0d0;"></i> SLA Risk</button>
      <button class="sn-chip" onclick="SNC.q('Summarize all billing and refund complaints today')"><i class="fa-solid fa-hand-holding-dollar" style="color:#059669;"></i> Billing</button>`;
      
    const custChips = `
      <button class="sn-chip" onclick="SNC.q('How do I submit a new complaint or warranty claim?')"><i class="fa-solid fa-file-circle-plus" style="color:#059669;"></i> Submit Ticket</button>
      <button class="sn-chip" onclick="SNC.q('When and how will I receive my refund?')"><i class="fa-solid fa-sack-dollar" style="color:#eef0d0;"></i> Refund Status</button>
      <button class="sn-chip" onclick="SNC.q('My package has not arrived yet - track delivery')"><i class="fa-solid fa-truck-fast" style="color:#d97706;"></i> Delivery Delay</button>
      <button class="sn-chip" onclick="SNC.q('My product has a defect or arrived damaged')"><i class="fa-solid fa-screwdriver-wrench" style="color:#f59e0b;"></i> Product Defect</button>
      <button class="sn-chip" onclick="SNC.q('My device battery is swelling or overheating')"><i class="fa-solid fa-battery-half" style="color:#e11d48;"></i> Battery Safety</button>`;

    const officerImg = isAdmin
      ? 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=80&auto=format&fit=crop&q=80'
      : 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&auto=format&fit=crop&q=80';
    const officerName = isAdmin ? 'Rayyan Ahmed Khan' : 'Marcus Chen';
    const officerRole = isAdmin ? 'CEO & Operations Director' : 'Lead Triage Specialist';

    const html = `
<div id="snLauncher" onclick="SNC.toggle()" title="Engage ${T.name}" role="button" aria-label="Open SupportNova AI Assistant">
  <div id="snAura"></div>
  <div id="snHUD">
    ${jarvisReactorSVG(64, 'L')}
  </div>
  <div id="snBadge">1</div>
</div>

<!-- Holographic Transparent Chat Terminal -->
<div id="snWin" role="dialog" aria-label="${T.name}">
  <div id="snHUDGrid"></div>
  <div id="snScan"></div>
  
  <!-- Holographic Header -->
  <div id="snHeader">
    <div class="sn-avatar-wrap">
      ${jarvisReactorSVG(38, 'H')}
    </div>
    <div style="flex: 1; min-width: 0;">
      <div id="snBotName">
        <span>${T.name}</span>
        <span class="sn-mode-tag">${T.modeTag}</span>
      </div>
      <div id="snStatus">
        <span class="sn-dot" id="snDot"></span>
        <span id="snStatusTxt">${T.role}</span>
      </div>
    </div>
    <div style="display: flex; gap: 6px;">
      <button class="sn-hbtn" id="snSndBtn" onclick="SNC.toggleSound()" title="Toggle Holographic Sound FX"><i class="fa-solid fa-bell"></i></button>
      <button class="sn-hbtn" id="snTtsBtnHdr" onclick="SNC.toggleTTS()" title="Toggle Voice Output"><i class="fa-solid fa-volume-high"></i></button>
      <button class="sn-hbtn" onclick="SNC.clearChat()" title="Reset Session"><i class="fa-solid fa-rotate-right"></i></button>
      <button class="sn-hbtn" onclick="SNC.toggle()" title="Close HUD"><i class="fa-solid fa-xmark"></i></button>
    </div>
  </div>

  <!-- Admin Portal Access Bar -->
  <div id="snPortal" style="display: ${isAdmin ? 'flex' : 'none'};">
    <span style="font-size: 0.72rem; color: #eef0d0; font-weight: 800; font-family:'JetBrains Mono',monospace;">PORTAL HUD</span>
    <a href="/" target="_blank" class="sn-portal-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> Customer Portal</a>
    <a href="/login" target="_blank" class="sn-portal-btn"><i class="fa-solid fa-user-shield"></i> Auth Gate</a>
    <span style="margin-left: auto; font-size: 0.72rem; color: #10b981; display: flex; align-items: center; gap: 5px; font-weight: 700; font-family:'JetBrains Mono',monospace;">
      <span style="width: 6px; height: 6px; background: #10b981; border-radius: 50%; box-shadow:0 0 6px #10b981;"></span>QUANTUM LINK ONLINE
    </span>
  </div>

  <div style="padding: 8px 12px 0; flex-shrink: 0; display: flex; justify-content: center;">
    <div class="sn-wa-toggle-bar" id="snModeToggle">
      <button class="sn-wa-tab active" id="snTabAI" onclick="SNC.switchTab('ai')">
        <i class="fa-solid fa-robot"></i> NovaBot AI
      </button>
      <button class="sn-wa-tab" id="snTabLive" onclick="SNC.switchTab('live')">
        <i class="fa-solid fa-comments"></i> Direct Support
      </button>
    </div>
  </div>

  <div id="snChips">${isAdmin ? adminChips : custChips}</div>

  <!-- Messages Container -->
  <div id="snMsgs">
    <!-- Boot Screen -->
    <div id="snBoot">
      <div class="sn-boot-reactor">${jarvisReactorSVG(76, 'B')}</div>
      <div class="sn-boot-label">${T.bootText}</div>
      <div class="sn-boot-sub">${T.bootSub}</div>
      <div class="sn-boot-bar"></div>
    </div>

    <div id="snTyping">
      <div class="sn-typing-bubble">
        <div class="sn-quantum-nodes">
          <div class="sn-qnode"></div>
          <div class="sn-qnode"></div>
          <div class="sn-qnode"></div>
        </div>
        <div class="sn-tlabel">ANALYZING QUANTUM MATRIX & RESOLUTION POLICIES...</div>
      </div>
    </div>
  </div>

  <div id="snLiveChat">
    <div class="sn-wa-header">
      <img class="sn-wa-officer-avatar" src="${officerImg}" alt="${officerName}">
      <div>
        <div class="sn-wa-officer-name">${officerName}</div>
        <div class="sn-wa-officer-role">
          <span class="sn-wa-online-dot"></span>
          ${officerRole} â€¢ Online
        </div>
      </div>
      <button onclick="SNC.initiateCall()" style="margin-left: auto; background: linear-gradient(135deg, #25d366, #128c7e); border: none; color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 0.76rem; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(37,211,102,0.4);" title="Start Internet Call"><i class="fa-solid fa-phone"></i> Call</button> <a href="/communication" target="_blank" style="margin-left: 6px; background: rgba(37,211,102,0.2); border: 1px solid rgba(37,211,102,0.4); color: #25d366; padding: 4px 10px; border-radius: 8px; font-size: 0.70rem; font-weight: 800; text-decoration: none; transition: all 0.2s ease;">Open Hub</a>
    </div>
    <div id="snWaMsgs">
      <div class="sn-wa-sys">Direct secure channel established</div>
      <div class="sn-wa-typing" id="snWaTyping">
        <div class="sn-wa-typing-bubble">
          <div class="sn-wa-dot"></div>
          <div class="sn-wa-dot"></div>
          <div class="sn-wa-dot"></div>
        </div>
      </div>
    </div>
    <div class="sn-wa-input-row">
      <input id="snWaInput" type="text" placeholder="Message ${officerName}..." onkeydown="SNC.waKey(event)">
      <button id="snWaSend" onclick="SNC.waSend()" title="Send"><i class="fa-solid fa-paper-plane"></i></button>
    </div>
  </div>

  <div id="snVoice">
    <div class="sn-vbars">
      <div class="sn-vbar"></div><div class="sn-vbar"></div><div class="sn-vbar"></div>
      <div class="sn-vbar"></div><div class="sn-vbar"></div><div class="sn-vbar"></div>
      <div class="sn-vbar"></div><div class="sn-vbar"></div><div class="sn-vbar"></div>
    </div>
    <div id="snVoicePulse">
      ${jarvisReactorSVG(90, 'V')}
    </div>
    <div id="snVoiceLabel">NOVABOT LISTENING...</div>
    <div id="snVoiceSub">State your inquiry or triage command clearly</div>
    <button class="sn-vstop" onclick="SNC.stopVoice()"><i class="fa-solid fa-microphone-slash"></i> STOP AUDIO</button>
  </div>

  <!-- Input Dock -->
  <div id="snInputArea">
    <textarea id="snInput" rows="1"
      placeholder="Query ${T.name}... (Press Enter to send)"
      onkeydown="SNC.key(event)"
      oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,96)+'px';"
    ></textarea>
    <button id="snMic"  class="sn-ibtn" onclick="SNC.toggleVoice()" title="Voice Input"><i class="fa-solid fa-microphone"></i></button>
    <button id="snTts"  class="sn-ibtn" onclick="SNC.toggleTTS()"   title="Speech Output"><i class="fa-solid fa-volume-xmark"></i></button>
    <button id="snSend" class="sn-ibtn" onclick="SNC.send()"         title="Transmit Command (Enter)"><i class="fa-solid fa-paper-plane"></i></button>
  </div>
</div>`;

    const wrap = document.createElement('div');
    wrap.id = 'snRoot';
    wrap.innerHTML = html;
    document.body.appendChild(wrap);
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     MESSAGE HANDLERS & TYPEWRITER FX
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function appendMsg(content, role, time, isVoice) {
    const box = document.getElementById('snMsgs');
    const typing = document.getElementById('snTyping');
    const boot = document.getElementById('snBoot');
    if (!box) return;
    if (boot) boot.remove();

    const ts = time || new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const wrap = document.createElement('div');
    wrap.className = 'sn-wrap';

    if (role === 'user') {
      playSciFiSound('send');
      wrap.innerHTML = `
        <div class="sn-user">
          ${isVoice ? '<i class="fa-solid fa-microphone" style="opacity:0.85; font-size:0.75rem; margin-right:6px; color:#eef0d0;"></i>' : ''}${escHtml(content)}
        </div>
        <div class="sn-time r"><i class="fa-solid fa-check-double" style="font-size:0.65rem; color:#eef0d0;"></i> ${ts}</div>`;
    } else if (role === 'bot') {
      playSciFiSound('recv');
      const id = 'snm' + Date.now();
      wrap.innerHTML = `
        <div class="sn-bot" id="${id}"></div>
        <div class="sn-time">
          <i class="fa-solid fa-atom" style="font-size:0.68rem; color:#eef0d0;"></i> ${ts}
          <button class="sn-speak-btn" onclick="SNC.speakEl('${id}')" title="Read aloud">
            <i class="fa-solid fa-volume-low"></i>
          </button>
        </div>`;
      if (typing) box.insertBefore(wrap, typing);
      else box.appendChild(wrap);
      box.scrollTop = box.scrollHeight;
      typewriter(document.getElementById(id), content);
      return;
    } else {
      wrap.innerHTML = `<div class="sn-sys">${content}</div>`;
    }

    if (typing) box.insertBefore(wrap, typing);
    else box.appendChild(wrap);
    box.scrollTop = box.scrollHeight;
  }

  function typewriter(el, text) {
    if (!el) return;
    const rendered = md(text);
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.25s ease-in-out';
    el.innerHTML = rendered;
    requestAnimationFrame(() => {
      el.style.opacity = '1';
      const b = document.getElementById('snMsgs');
      if (b) b.scrollTop = b.scrollHeight;
    });
    if (ttsActive) speakText(text);
  }

  function showTyping() {
    const boot = document.getElementById('snBoot');
    if (boot) boot.remove();
    const el = document.getElementById('snTyping');
    if (el) {
      el.style.display = 'flex';
      const b = document.getElementById('snMsgs');
      if (b) { b.appendChild(el); b.scrollTop = b.scrollHeight; }
    }
    setProcessing(true);
  }

  function hideTyping() {
    const el = document.getElementById('snTyping');
    if (el) el.style.display = 'none';
    setProcessing(false);
  }

  function setProcessing(on) {
    const hud = document.getElementById('snHUD');
    if (!hud) return;
    if (on) hud.classList.add('processing');
    else hud.classList.remove('processing');
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     VOICE RECOGNITION (STT) & SYNTHESIS (TTS)
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function initRecog() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.lang = 'en-US';
    r.onresult = e => {
      const t = e.results[0][0].transcript;
      stopVoiceUI();
      const inp = document.getElementById('snInput');
      if (inp) inp.value = t;
      setTimeout(() => SNC.send(true), 200);
    };
    r.onerror = () => stopVoiceUI();
    r.onend = () => stopVoiceUI();
    return r;
  }

  function startVoiceUI() {
    document.getElementById('snVoice')?.classList.add('on');
    document.getElementById('snMic')?.classList.add('rec');
    voiceOn = true;
    playSciFiSound('open');
  }

  function stopVoiceUI() {
    document.getElementById('snVoice')?.classList.remove('on');
    document.getElementById('snMic')?.classList.remove('rec');
    voiceOn = false;
    if (recog) {
      try { recog.stop(); } catch (e) {}
    }
  }

  function speakText(text) {
    if (!tts || !ttsActive) return;
    tts.cancel();
    const clean = text
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/`(.+?)`/g, '$1')
      .replace(/<[^>]+>/g, '')
      .replace(/[â€¢\-] /g, '');
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 1.05;
    u.pitch = 1.04;
    u.volume = 0.95;
    const v = tts.getVoices();
    const pref = v.find(x => x.name.includes('Google') && x.lang === 'en-US') ||
                 v.find(x => x.name.includes('Natural') && x.lang === 'en-US') ||
                 v.find(x => x.lang === 'en-US') || v[0];
    if (pref) u.voice = pref;
    tts.speak(u);
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     REAL-TIME WEBSOCKET COMMUNICATOR
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function connect() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${location.host}/ws/chat?mode=${mode}`;
    try {
      ws = new WebSocket(url);
      ws.onopen = () => { retries = 0; setStatus('Quantum Link Online', true); };
      ws.onmessage = onMsg;
      ws.onclose = onClose;
      ws.onerror = () => setStatus('Connection Error', false);
    } catch (e) {
      console.error('[SNC] WS Error:', e);
    }
  }

  function onMsg(ev) {
    try {
      const d = JSON.parse(ev.data);
      if (d.type === 'welcome') {
        hideTyping();
        appendMsg(d.content, 'bot', 'Just now');
      } else if (d.type === 'typing') {
        showTyping();
      } else if (d.type === 'response') {
        hideTyping();
        appendMsg(d.content, 'bot', d.timestamp);
        unlock();
      } else if (d.type === 'error') {
        hideTyping();
        appendMsg('âš  ' + d.content, 'system');
        unlock();
      }
    } catch (e) {}
  }

  function onClose() {
    setStatus('Reconnecting...', false);
    if (retries < MAX_RETRY) {
      retries++;
      setTimeout(connect, 1800 * retries);
    } else {
      setStatus('Offline', false);
    }
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     UI HELPERS & LOCKING
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function setStatus(txt, online) {
    const dot = document.getElementById('snDot');
    const lbl = document.getElementById('snStatusTxt');
    if (dot) {
      dot.style.background = online ? '#eef0d0' : '#e11d48';
      dot.style.boxShadow = online ? '0 0 10px #eef0d0' : '0 0 10px #e11d48';
    }
    if (lbl && txt) lbl.textContent = txt;
  }

  function lock() {
    locked = true;
    const b = document.getElementById('snSend');
    const i = document.getElementById('snInput');
    if (b) b.disabled = true;
    if (i) i.disabled = true;
  }

  function unlock() {
    locked = false;
    const b = document.getElementById('snSend');
    const i = document.getElementById('snInput');
    if (b) b.disabled = false;
    if (i) { i.disabled = false; i.focus(); }
  }

  function escHtml(t) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(t));
    return d.innerHTML;
  }

  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     PUBLIC API EXPOSURE
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function waTs() {
    return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }

  function waAppendMsg(text, side) {
    const box = document.getElementById('snWaMsgs');
    const typingEl = document.getElementById('snWaTyping');
    if (!box) return;
    const wrap = document.createElement('div');
    wrap.className = 'sn-wa-msg-wrap';
    const ts = waTs();
    if (side === 'out') {
      wrap.innerHTML = `
        <div class="sn-wa-bubble-out">${escHtml(text)}</div>
        <div class="sn-wa-meta">${ts} <span class="sn-wa-ticks"><i class="fa-solid fa-check-double" style="color:#53bdeb;font-size:0.72rem;"></i></span></div>`;
    } else {
      wrap.innerHTML = `
        <div class="sn-wa-bubble-in">${escHtml(text)}</div>
        <div class="sn-wa-meta in-meta">${ts}</div>`;
    }
    if (typingEl) box.insertBefore(wrap, typingEl);
    else box.appendChild(wrap);
    box.scrollTop = box.scrollHeight;
  }

  function waShowTyping(on) {
    const el = document.getElementById('snWaTyping');
    if (el) el.className = on ? 'sn-wa-typing on' : 'sn-wa-typing';
  }

  async function waStartSession() {
    try {
      const r = await fetch('/api/chat/live/messages');
      const d = await r.json();
      liveConvId = d.client_id || 'guest_client_001';
      (d.messages || []).forEach(m => {
        const side = (m.sender === 'customer') ? 'out' : 'in';
        const text = m.message || m.content || '';
        if (text) waAppendMsg(text, side);
      });
    } catch (e) {}
    if (!livePollTimer) livePollTimer = setInterval(waPollMessages, 3500);
  }

  let _lastPollTs = Date.now();

  async function waPollMessages() {
    if (!liveConvId) return;
    try {
      const r = await fetch(`/api/chat/live/messages?client_id=${encodeURIComponent(liveConvId)}`);
      const d = await r.json();
      const now = Date.now();
      (d.messages || []).forEach(m => {
        const msgTs = new Date(m._id ? parseInt(m._id.split('_').pop()) * 1000 : 0).getTime();
        if (m.sender !== 'customer' && msgTs > _lastPollTs - 4000) {
          const text = m.message || m.content || '';
          if (text) waAppendMsg(text, 'in');
        }
      });
      _lastPollTs = now;
    } catch (e) {}
  }

  async function waSendMessage(text) {
    waAppendMsg(text, 'out');
    waShowTyping(true);
    try {
      const r = await fetch('/api/chat/live/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, client_id: liveConvId, sender: 'customer' })
      });
      const d = await r.json();
      if (!liveConvId) {
        const cid = (d.message || {}).client_id;
        if (cid) {
          liveConvId = cid;
          if (!livePollTimer) livePollTimer = setInterval(waPollMessages, 3500);
        }
      }
    } catch (e) {}
    setTimeout(() => waShowTyping(false), 400);
  }

  window.SNC = {
    toggle() {
      const win = document.getElementById('snWin');
      const badge = document.getElementById('snBadge');
      if (!win) return;
      open = !open;
      playSciFiSound(open ? 'open' : 'click');
      if (open) {
        win.style.display = 'flex';
        win.style.flexDirection = 'column';
        win.style.animation = 'snPanelEntrance 0.38s cubic-bezier(0.34, 1.56, 0.64, 1) forwards';
        if (badge) badge.style.display = 'none';
        if (!ws || ws.readyState > 1) connect();
        setTimeout(() => document.getElementById('snInput')?.focus(), 360);
      } else {
        win.style.animation = 'snPanelExit 0.24s ease forwards';
        setProcessing(false);
        setTimeout(() => { win.style.display = 'none'; }, 240);
      }
    },

    toggleSound() {
      soundOn = !soundOn;
      const btn = document.getElementById('snSndBtn');
      if (btn) {
        btn.innerHTML = soundOn ? '<i class="fa-solid fa-bell"></i>' : '<i class="fa-solid fa-bell-slash"></i>';
        btn.style.opacity = soundOn ? '1' : '0.6';
      }
      playSciFiSound('click');
    },

    send(isVoice) {
      const inp = document.getElementById('snInput');
      if (!inp) return;
      const msg = inp.value.trim();
      if (!msg || locked) return;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        connect();
        setTimeout(() => SNC.send(isVoice), 800);
        return;
      }
      appendMsg(msg, 'user', null, isVoice);
      inp.value = '';
      inp.style.height = 'auto';
      lock();
      ws.send(JSON.stringify({ message: msg }));
    },

    q(msg) {
      playSciFiSound('click');
      const inp = document.getElementById('snInput');
      if (inp) inp.value = msg;
      this.send();
    },

    key(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    },

    toggleVoice() {
      if (voiceOn) {
        stopVoiceUI();
        return;
      }
      if (!recog) recog = initRecog();
      if (!recog) {
        appendMsg('Voice input requires Chrome or Edge browser.', 'system');
        return;
      }
      startVoiceUI();
      try { recog.start(); } catch (e) { stopVoiceUI(); }
    },

    stopVoice() {
      stopVoiceUI();
    },

    toggleTTS() {
      ttsActive = !ttsActive;
      playSciFiSound('click');
      const btn = document.getElementById('snTts');
      const hdr = document.getElementById('snTtsBtnHdr');
      if (btn) {
        btn.className = `sn-ibtn${ttsActive ? ' on' : ''}`;
        btn.innerHTML = ttsActive ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark"></i>';
      }
      if (hdr) hdr.style.opacity = ttsActive ? '1' : '0.6';
      appendMsg(ttsActive ? 'Neural Speech Synthesis output enabled.' : 'Speech output muted.', 'system');
    },

    speakEl(id) {
      const el = document.getElementById(id);
      if (!el) return;
      el.classList.add('speaking');
      setTimeout(() => el.classList.remove('speaking'), 4000);
      const t = el.innerText || el.textContent;
      if (!tts) return;
      tts.cancel();
      const u = new SpeechSynthesisUtterance(t);
      u.rate = 1.05;
      u.pitch = 1.04;
      const v = tts.getVoices();
      const pref = v.find(x => x.name.includes('Google') && x.lang === 'en-US') ||
                   v.find(x => x.name.includes('Natural') && x.lang === 'en-US') ||
                   v.find(x => x.lang === 'en-US') || v[0];
      if (pref) u.voice = pref;
      tts.speak(u);
    },

    clearChat() {
      playSciFiSound('click');
      const box = document.getElementById('snMsgs');
      if (box) {
        box.innerHTML = `
          <div id="snTyping">
            <div class="sn-typing-bubble">
              <div class="sn-quantum-nodes">
                <div class="sn-qnode"></div>
                <div class="sn-qnode"></div>
                <div class="sn-qnode"></div>
              </div>
              <div class="sn-tlabel">ANALYZING QUANTUM MATRIX & RESOLUTION POLICIES...</div>
            </div>
          </div>`;
        appendMsg('Neural conversation session refreshed.', 'system');
      }
      if (ws) ws.close();
      setTimeout(connect, 400);
    },

    switchTab(tab) {
      const aiPanel  = document.getElementById('snMsgs');
      const waPanel  = document.getElementById('snLiveChat');
      const inputDock= document.getElementById('snInputArea');
      const chipsBar = document.getElementById('snChips');
      const tabAI    = document.getElementById('snTabAI');
      const tabLive  = document.getElementById('snTabLive');
      if (tab === 'live') {
        liveMode = true;
        if (aiPanel)   { aiPanel.style.display = 'none'; }
        if (inputDock) { inputDock.style.display = 'none'; }
        if (chipsBar)  { chipsBar.style.display = 'none'; }
        if (waPanel)   { waPanel.classList.add('active'); }
        if (tabAI)     { tabAI.className = 'sn-wa-tab'; }
        if (tabLive)   { tabLive.className = 'sn-wa-tab wa-active'; }
        if (!liveConvId) waStartSession();
        const wi = document.getElementById('snWaInput');
        if (wi) setTimeout(() => wi.focus(), 200);
      } else {
        liveMode = false;
        if (livePollTimer) { clearInterval(livePollTimer); livePollTimer = null; }
        if (aiPanel)   { aiPanel.style.display = 'flex'; }
        if (inputDock) { inputDock.style.display = 'flex'; }
        if (chipsBar)  { chipsBar.style.display = 'flex'; }
        if (waPanel)   { waPanel.classList.remove('active'); }
        if (tabAI)     { tabAI.className = 'sn-wa-tab active'; }
        if (tabLive)   { tabLive.className = 'sn-wa-tab'; }
        setTimeout(() => document.getElementById('snInput')?.focus(), 200);
      }
    },

    waSend() {
      const inp = document.getElementById('snWaInput');
      if (!inp) return;
      const msg = inp.value.trim();
      if (!msg) return;
      inp.value = '';
      playSciFiSound('send');
      waSendMessage(msg);
    },

    async initiateCall() {
      try {
        const r = await fetch('/api/call/initiate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ client_id: 'USR-CUSTOMER', client_name: 'Valued Customer' })
        });
        const d = await r.json();
        if (d.status === 'unavailable') {
          if(typeof showToast==='function') showToast('⚠️ OWNER IS NOT AVAILABLE: No staff members are online', 'error');
        } else if (d.status === 'ringing') {
          if(typeof showToast==='function') showToast('📞 Call placed to ' + (d.target_staff ? d.target_staff.name : 'Staff'), 'info');
        }
      } catch(e) {
        if(typeof showToast==='function') showToast('Call failed to initiate.', 'error');
      }
    },
    waKey(e) {
      if (e.key === 'Enter') { e.preventDefault(); this.waSend(); }
    }
  };


  /* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
     INITIALIZATION ON LOAD
  â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
  function init() {
    mode = detectMode();
    const isAdmin = mode === 'admin';
    const T = theme(isAdmin);
    injectCSS();
    buildHTML(T, isAdmin);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();



