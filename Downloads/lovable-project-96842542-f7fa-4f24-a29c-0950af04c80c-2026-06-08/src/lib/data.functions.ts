import { apiFetch } from "@/lib/api/client";

export async function listMyResumes() {
  return apiFetch<
    Array<{
      id: string;
      title: string;
      ats_score: number | null;
      health_score: number | null;
      file_name: string | null;
      analyzed_at: string | null;
      created_at: string;
      summary: string | null;
    }>
  >("/api/resumes");
}

export async function getResume(data: { id: string }) {
  return apiFetch<Record<string, unknown>>(`/api/resumes/${data.id}`);
}

export async function deleteResume(data: { id: string }) {
  return apiFetch<{ ok: boolean }>(`/api/resumes/${data.id}`, {
    method: "DELETE",
  });
}

export async function getMyMatches() {
  return apiFetch<
    Array<{
      id: string;
      match_score: number;
      recommendation: string | null;
      created_at: string;
      matched_skills: string[];
      missing_skills: string[];
      resume_id: string;
      job_description_id: string;
      job_descriptions: { title: string; company: string | null };
      resumes: { title: string };
    }>
  >("/api/matches");
}

export async function getMyRole() {
  return apiFetch<{
    roles: string[];
    isRecruiter: boolean;
    isAdmin: boolean;
  }>("/api/role");
}

export async function setMyRole(data: { role: "job_seeker" | "recruiter" }) {
  return apiFetch<{ ok: boolean }>("/api/role", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listCandidates() {
  return apiFetch<
    Array<{
      id: string;
      title: string;
      ats_score: number | null;
      health_score: number | null;
      summary: string | null;
      skills: string[];
      created_at: string;
      user_id: string;
    }>
  >("/api/candidates");
}
