import http from "./client";

export const createScene = (payload) => http.post("/api/scenes", payload);
export const listScenes = () => http.get("/api/scenes");
export const getScene = (id) => http.get(`/api/scenes/${id}`);
export const updateScene = (id, payload) => http.put(`/api/scenes/${id}`, payload);
