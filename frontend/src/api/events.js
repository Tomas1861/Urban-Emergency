import http from "./client";

export const listEvents = (activityId) => http.get("/api/events", { params: { activity_id: activityId } });
export const createEvent = (payload) => http.post("/api/events", payload);
export const getEvent = (id) => http.get(`/api/events/${id}`);
export const updateEvent = (id, payload) => http.put(`/api/events/${id}`, payload);
export const analyzeEvent = (id) => http.post(`/api/events/${id}/analyze`);
export const confirmEvent = (id) => http.post(`/api/events/${id}/confirm`);
export const closeEvent = (id) => http.post(`/api/events/${id}/close`);
export const getExecutionSummary = (id) => http.get(`/api/events/${id}/execution-summary`);

export const retrieveKnowledge = (eventId) => http.post(`/api/events/${eventId}/retrieve-knowledge`);
export const updateRetrievalSelection = (eventId, payload) =>
  http.put(`/api/events/${eventId}/retrieval-selection`, payload);

export const generatePlan = (eventId, payload = {}) =>
  http.post(`/api/events/${eventId}/generate-plan`, payload);
export const generateReport = (eventId, payload = {}) =>
  http.post(`/api/events/${eventId}/generate-report`, payload);
