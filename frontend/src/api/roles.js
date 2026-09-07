import http from "./client";

export const listRoles = () => http.get("/api/roles");
export const createRole = (payload) => http.post("/api/roles", payload);
