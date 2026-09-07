import http from "./client";

export const buildDocumentGraph = (documentId) => http.post(`/api/graph/documents/${documentId}/build`);
export const getGraph = (documentId) => http.get("/api/graph/graph", { params: { document_id: documentId } });
export const searchGraph = (q) => http.get("/api/graph/search", { params: { q } });
export const getGraphStats = () => http.get("/api/graph/stats");
