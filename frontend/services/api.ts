import type { DashboardStats, DocumentRecord } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface ScreenResponse {
  document_id: number;
  filename: string;
  status: string;
  message: string;
}

export async function screenDocument(
  documentType: string,
  file: File
): Promise<ScreenResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ScreenResponse>(
    `/api/screening/documents?document_type=${documentType}`,
    { method: "POST", body: formData }
  );
}

export async function getScreeningResult(id: number): Promise<DocumentRecord> {
  return request<DocumentRecord>(`/api/screening/${id}`);
}

export async function getScreeningHistory(): Promise<DocumentRecord[]> {
  return request<DocumentRecord[]>("/api/screening/results");
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/dashboard/stats");
}

export function getRiskVariant(level?: string) {
  switch (level) {
    case "low":
      return "success";
    case "medium":
      return "warning";
    case "high":
      return "destructive";
    case "critical":
      return "critical";
    default:
      return "secondary";
  }
}

export function getStatusVariant(status?: string) {
  switch (status) {
    case "cleared":
    case "approved":
      return "success";
    case "flagged":
    case "rejected":
      return "destructive";
    case "review":
      return "warning";
    default:
      return "secondary";
  }
}

export function formatLabel(str?: string) {
  if (!str) return "";
  return str
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
