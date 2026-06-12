import { apiFetch } from "@/lib/api/client";

export async function importResumeFromUrl(data: { url: string; title?: string }) {
  return apiFetch<{
    id: string;
    title: string;
    raw_text: string;
    file_name: string | null;
    ats_score: number;
    health_score: number;
    summary: string;
    skills: string[];
    experience: Array<{ role: string; company: string; duration: string }>;
    education: Array<{ degree: string; institution: string; year: string }>;
    missing_keywords: string[];
    suggestions: Array<{ category: string; title: string; detail: string }>;
    analyzed_at: string;
    created_at: string;
    updated_at: string;
    user_id: string;
  }>("/api/resumes/import-url", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
