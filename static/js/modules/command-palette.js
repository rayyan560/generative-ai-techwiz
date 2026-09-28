import { showToast } from './toasts.js';

export function initCommandPalette() {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      toggleCommandPalette();
    }
  });
}

export function toggleCommandPalette() {
  let modal = document.getElementById('commandPaletteModal');
  if (!modal) {
    createCommandPaletteDOM();
    modal = document.getElementById('commandPaletteModal');
  }
  if (modal.style.display === 'flex') {
    modal.style.display = 'none';
  } else {
    modal.style.display = 'flex';
    const input = document.getElementById('cmdPaletteInput');
    if (input) input.focus();
  }
}

function createCommandPaletteDOM() {
  const modal = document.createElement('div');
  modal.id = 'commandPaletteModal';
  modal.className = 'modal-backdrop';
  modal.style.display = 'none';

  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-lg" style="max-width: 640px;">
      <div class="modal-header">
        <div style="position: relative; width: 100%;">
          <i class="fa-solid fa-magnifying-glass" style="position: absolute; left: 14px; top: 14px; color: var(--text-muted);"></i>
          <input type="text" id="cmdPaletteInput" placeholder="Type a command or search ticket ID... (Ctrl+K)" style="width: 100%; padding: 12px 14px 12px 42px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-card); color: var(--text-main); font-size: 0.95rem;">
        </div>
      </div>
      <div class="modal-body" style="max-height: 320px; overflow-y: auto;">
        <div class="cmd-list" id="cmdPaletteList">
          <div class="cmd-item" onclick="window.location.href='/admin'" style="padding: 10px 14px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
            <i class="fa-solid fa-gauge-high"></i> Go to Admin Dashboard
          </div>
          <div class="cmd-item" onclick="window.location.href='/'" style="padding: 10px 14px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
            <i class="fa-solid fa-headset"></i> Go to Customer Portal
          </div>
          <div class="cmd-item" onclick="window.location.href='/refunds'" style="padding: 10px 14px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
            <i class="fa-solid fa-receipt"></i> Financial Escrow & Refunds
          </div>
          <div class="cmd-item" onclick="window.location.href='/knowledge'" style="padding: 10px 14px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
            <i class="fa-solid fa-book"></i> Knowledge Base & Policy Auditor
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}
