import { SoundFX } from './audio.js';

export function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '<i class="fa-solid fa-circle-info"></i>';
  if (type === 'success') {
    icon = '<i class="fa-solid fa-circle-check"></i>';
    SoundFX.playSuccess();
  } else if (type === 'error') {
    icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    SoundFX.playPing();
  } else if (type === 'warning') {
    icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    SoundFX.playPing();
  } else {
    SoundFX.playClick();
  }

  toast.innerHTML = `
    <div class="toast-content">
      <span class="toast-icon">${icon}</span>
      <span class="toast-message">${message}</span>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-fadeout');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
