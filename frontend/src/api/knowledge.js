import http from "./client";

export const listDocuments = () => http.get("/api/knowledge/documents");
export const getDocument = (id) => http.get(`/api/knowledge/documents/${id}`);
export const updateDocument = (id, params) =>
  http.put(`/api/knowledge/documents/${id}`, null, { params });
export const deleteDocument = (id) => http.delete(`/api/knowledge/documents/${id}`);

export const uploadDocument = (file, title, category) => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("category", category);
  return http.post("/api/knowledge/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
