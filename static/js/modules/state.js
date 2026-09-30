/**
 * SupportNova State Management Module
 */
export const store = {
  currentComplaints: [],
  selectedComplaintId: null,
  selectedCommComplaintId: null,
  currentCommThreads: [],
  currentRefundRecords: [],
  isOnCall: false,
  soundEnabled: true,
  wsConnection: null,

  setComplaints(complaints) {
    this.currentComplaints = complaints || [];
  },

  setSelectedComplaintId(id) {
    this.selectedComplaintId = id;
  },

  setCommThreads(threads) {
    this.currentCommThreads = threads || [];
  },

  setRefundRecords(records) {
    this.currentRefundRecords = records || [];
  },

  setWebSocket(ws) {
    this.wsConnection = ws;
  }
};
