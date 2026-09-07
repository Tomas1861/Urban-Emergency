import http from "./client";

export const findPlanByEvent = (eventId) => http.get("/api/plans", { params: { event_id: eventId } });
export const getPlan = (id) => http.get(`/api/plans/${id}`);
export const listPlanVersions = (id) => http.get(`/api/plans/${id}/versions`);
export const saveManualPlanVersion = (id, content, changeSummary) =>
  http.post(`/api/plans/${id}/versions`, content, { params: { change_summary: changeSummary } });
export const regeneratePlanSection = (id, payload) =>
  http.post(`/api/plans/${id}/regenerate-section`, payload);
export const confirmPlan = (id, confirmedBy) =>
  http.post(`/api/plans/${id}/confirm`, null, { params: { confirmed_by: confirmedBy } });

export const exportPlanUrl = (id) =>
  `${import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"}/api/plans/${id}/export`;
