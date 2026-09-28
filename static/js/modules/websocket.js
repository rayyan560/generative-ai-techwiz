import { store } from './state.js';
import { showToast } from './toasts.js';

export function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/triage`;

  try {
    const ws = new WebSocket(wsUrl);
    store.setWebSocket(ws);

    ws.onopen = () => {
      console.log('SupportNova Live WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'NEW_COMPLAINT') {
          showToast(`🚨 New Complaint ${data.complaint_id} received from ${data.customer_name}`, 'warning');
          if (typeof window.refreshDashboardData === 'function') {
            window.refreshDashboardData();
          }
        } else if (data.type === 'TRIAGE_ACTION_EXECUTED') {
          showToast(`⚡ Ticket ${data.complaint_id} updated: ${data.action}`, 'info');
        } else if (data.type === 'INCOMING_CALL') {
          showToast(`📞 Incoming call from ${data.call.client_name}`, 'info');
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      console.warn('WebSocket closed, attempting reconnect in 5s...');
      setTimeout(initWebSocket, 5000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket connection error:', err);
    };
  } catch (e) {
    console.error('Failed to initialize WebSocket:', e);
  }
}
