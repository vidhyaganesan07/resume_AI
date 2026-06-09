import { apiFetch } from "@/lib/api/client";

export async function analyzeResume(data: {
  resumeId?: string;
  title: string;
  rawText: string;
  fileName?: string;
}) {
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
  }>("/api/resumes/analyze", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function matchResumeToJD(data: {
  resumeId: string;
  jdTitle: string;
  jdCompany?: string;
  jdText: string;
}) {
  return apiFetch<{
    match: {
      id: string;
      match_score: number;
      matched_skills: string[];
      missing_skills: string[];
      skill_match: { technical: number; experience: number; education: number };
      recommendation: string;
      resume_id: string;
      job_description_id: string;
      created_at: string;
    };
    jd: {
      id: string;
      title: string;
      company: string | null;
      raw_text: string;
      created_at: string;
    };
  }>("/api/matches", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function askAssistant(data: { resumeId?: string; question: string }) {
  return apiFetch<{ answer: string }>("/api/assistant", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
