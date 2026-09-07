import http from "./client";

export const findReportByEvent = (eventId) => http.get("/api/reports", { params: { event_id: eventId } });
export const getReport = (id) => http.get(`/api/reports/${id}`);
export const listReportVersions = (id) => http.get(`/api/reports/${id}/versions`);
export const saveManualReportVersion = (id, content, changeSummary) =>
  http.post(`/api/reports/${id}/versions`, content, { params: { change_summary: changeSummary } });
export const confirmReport = (id, confirmedBy) =>
  http.post(`/api/reports/${id}/confirm`, null, { params: { confirmed_by: confirmedBy } });
export const saveAsCase = (id) => http.post(`/api/reports/${id}/save-as-case`);

export const exportReportUrl = (id) =>
  `${import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"}/api/reports/${id}/export`;
