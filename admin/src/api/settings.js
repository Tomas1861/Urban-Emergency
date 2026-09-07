import http from "./client";

export const getLlmSettings = () => http.get("/api/settings/llm");
export const updateLlmSettings = (provider) => http.put("/api/settings/llm", null, { params: { provider } });
