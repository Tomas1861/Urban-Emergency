import http from "./client";

export const createActivity = (payload) => http.post("/api/activities", payload);
export const listActivities = () => http.get("/api/activities");
export const getActivity = (id) => http.get(`/api/activities/${id}`);
export const updateActivity = (id, payload) => http.put(`/api/activities/${id}`, payload);
