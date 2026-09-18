import type { DocumentRecord, Extraction, ProcessingJob } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.error_message || JSON.stringify(data));
  return data as T;
}

export const api = {
  listDocuments: () => request<DocumentRecord[]>("/documents/"),
  getDocument: (id: string) => request<DocumentRecord>(`/documents/${id}/`),
  uploadDocument(file: File, onProgress: (progress: number) => void) {
    return new Promise<DocumentRecord>((resolve, reject) => {
      const form = new FormData();
      form.append("file", file);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_URL}/documents/`);
      xhr.upload.onprogress = (event) => event.lengthComputable && onProgress(Math.round((event.loaded / event.total) * 100));
      xhr.onload = () => {
        const data = JSON.parse(xhr.responseText || "{}");
        if (xhr.status >= 200 && xhr.status < 300) resolve(data as DocumentRecord);
        else reject(new Error(data.detail || JSON.stringify(data)));
      };
      xhr.onerror = () => reject(new Error("Upload failed"));
      xhr.send(form);
    });
  },
  extract: (id: number | string) => request<ProcessingJob>(`/documents/${id}/extract/`, { method: "POST" }),
  getExtraction: (id: number | string) => request<Extraction>(`/documents/${id}/extraction/`),
  updateExtraction: (id: number | string, data: Partial<Extraction>) => request<Extraction>(`/documents/${id}/extraction/`, { method: "PATCH", body: JSON.stringify(data) }),
  approve: (id: number | string) => request<DocumentRecord>(`/documents/${id}/approve/`, { method: "POST" }),
  automate: (id: number | string) => request<ProcessingJob>(`/documents/${id}/automate/`, { method: "POST" }),
};
