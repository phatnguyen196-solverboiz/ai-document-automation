import type { DocumentRecord, Extraction, ProcessingJob } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  constructor(message: string, readonly fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
  }
}

function parseError(data: unknown, fallback: string): ApiError {
  if (!data || typeof data !== "object") return new ApiError(fallback);
  const payload = data as Record<string, unknown>;
  const nested = payload.errors && typeof payload.errors === "object"
    ? payload.errors as Record<string, unknown>
    : payload;
  const fieldErrors: Record<string, string> = {};
  for (const [field, value] of Object.entries(nested)) {
    const message = Array.isArray(value) ? value[0] : value;
    if (typeof message === "string" && !["detail", "error_message"].includes(field)) fieldErrors[field] = message;
  }
  const firstField = Object.entries(fieldErrors)[0];
  const message = typeof payload.detail === "string"
    ? payload.detail
    : typeof payload.error_message === "string"
      ? payload.error_message
      : firstField
        ? `${firstField[0].replaceAll("_", " ")}: ${firstField[1]}`
        : fallback;
  return new ApiError(message, fieldErrors);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw parseError(data, `Request failed (${response.status})`);
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
        let data: unknown = {};
        try { data = JSON.parse(xhr.responseText || "{}"); } catch { /* non-JSON server response */ }
        if (xhr.status >= 200 && xhr.status < 300) resolve(data as DocumentRecord);
        else reject(parseError(data, `Upload failed (${xhr.status})`));
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
