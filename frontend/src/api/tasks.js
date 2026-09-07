import http from "./client";

export const generateTasks = (planId, payload = {}) =>
  http.post(`/api/plans/${planId}/generate-tasks`, payload);
export const listPlanTasks = (planId) => http.get(`/api/plans/${planId}/tasks`);
export const confirmTasks = (planId) => http.post(`/api/plans/${planId}/confirm-tasks`);

export const createTask = (planId, item) => http.post("/api/tasks", item, { params: { plan_id: planId } });
export const updateTask = (id, payload) => http.put(`/api/tasks/${id}`, payload);
export const deleteTask = (id) => http.delete(`/api/tasks/${id}`);
