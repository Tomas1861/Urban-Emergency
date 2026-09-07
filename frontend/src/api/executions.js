import http from "./client";

export const startTask = (id) => http.post(`/api/tasks/${id}/start`);
export const completeTask = (id) => http.post(`/api/tasks/${id}/complete`);
export const failTask = (id) => http.post(`/api/tasks/${id}/fail`);
export const cancelTask = (id) => http.post(`/api/tasks/${id}/cancel`);
export const updateExecution = (id, payload) => http.put(`/api/tasks/${id}/execution`, payload);
