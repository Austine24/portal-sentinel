import type { z } from "zod";
import {
  evidencePackageSchema,
  incidentListSchema,
  incidentSchema,
  syncResultSchema,
  type EvidencePackage,
  type Incident,
  type IncidentStatus,
  type SyncResult,
} from "./schemas";

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {}

async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    throw new ApiError("Cannot reach the Sentinel API. Is the backend running?");
  }

  if (!response.ok) {
    let detail = `The API returned status ${response.status}.`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // keep the generic message
    }
    throw new ApiError(detail);
  }

  const parsed = schema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ApiError("The API returned data in an unexpected shape.");
  }
  return parsed.data;
}

export function listIncidents(status?: IncidentStatus): Promise<Incident[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/incidents${query}`, incidentListSchema);
}

export function getIncident(id: number): Promise<Incident> {
  return request(`/api/incidents/${id}`, incidentSchema);
}

export function syncIncidents(): Promise<SyncResult> {
  return request("/api/incidents/sync", syncResultSchema, { method: "POST" });
}

export function changeStatus(id: number, status: IncidentStatus, note?: string): Promise<Incident> {
  return request(`/api/incidents/${id}/status`, incidentSchema, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, note: note || null }),
  });
}

export function prepareEvidence(id: number): Promise<EvidencePackage> {
  return request(`/api/incidents/${id}/evidence/prepare`, evidencePackageSchema, { method: "POST" });
}

export function getEvidence(id: number): Promise<EvidencePackage> {
  return request(`/api/incidents/${id}/evidence`, evidencePackageSchema);
}
