import { apiFetch } from "@/lib/api/client";

export async function rankCandidatesForJD(data: {
  jdTitle: string;
  jdText: string;
  limit?: number;
  filters?: {
    seniority?: string;
    mustHaveSkills?: string;
    niceToHaveSkills?: string;
    minYears?: number;
    workMode?: string;
    domain?: string;
    cultureNotes?: string;
  };
}) {
  return apiFetch<
    Array<{
      resume_id: string;
      title: string;
      ats_score: number;
      health_score: number;
      match_score: number;
      combined_score: number;
      matched_skills: string[];
      missing_skills: string[];
      reason: string;
    }>
  >("/api/ranking", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
