import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { matchResumeToJD } from "@/lib/ai.functions";
import { listMyResumes, getMyMatches } from "@/lib/data.functions";
import { ScoreRing } from "@/components/ScoreRing";
import { Target, Loader2 } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/app/match")({ component: Match });

function Match() {
  const qc = useQueryClient();

  const { data: resumes = [] } = useQuery({ queryKey: ["resumes"], queryFn: listMyResumes });
  const { data: matches = [] } = useQuery({ queryKey: ["matches"], queryFn: getMyMatches });

  const [resumeId, setResumeId] = useState("");
  const [jdTitle, setJdTitle] = useState("");
  const [jdCompany, setJdCompany] = useState("");
  const [jdText, setJdText] = useState("");
  type MatchResult = Awaited<ReturnType<typeof matchResumeToJD>>["match"];
  const [result, setResult] = useState<MatchResult | null>(null);

  const mut = useMutation({
    mutationFn: () => matchResumeToJD({ resumeId, jdTitle, jdCompany, jdText }),
    onSuccess: (r) => { setResult(r.match); qc.invalidateQueries({ queryKey: ["matches"] }); toast.success("Match complete!"); },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Match failed"),
  });

  const matched = (result?.matched_skills as string[]) ?? [];
  const missing = (result?.missing_skills as string[]) ?? [];

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Job Description Match</h1>
        <p className="text-muted-foreground mt-1">Match your resume to any JD with semantic AI scoring.</p>
      </header>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft space-y-3">
          <h2 className="font-semibold mb-2">New match</h2>
          <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
            <option value="">Select a resume…</option>
            {resumes.map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
          </select>
          <input value={jdTitle} onChange={(e) => setJdTitle(e.target.value)} placeholder="Job title" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
          <input value={jdCompany} onChange={(e) => setJdCompany(e.target.value)} placeholder="Company (optional)" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
          <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} rows={10} placeholder="Paste the job description…" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
          <button
            onClick={() => mut.mutate()}
            disabled={mut.isPending || !resumeId || jdText.length < 20 || !jdTitle}
            className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-4 py-2.5 text-sm font-medium shadow-elegant disabled:opacity-50"
          >
            {mut.isPending ? <><Loader2 className="size-4 animate-spin" /> Matching…</> : <><Target className="size-4" /> Run AI Match</>}
          </button>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-semibold mb-4">Result</h2>
          {!result ? (
            <p className="text-sm text-muted-foreground">Run a match to see results here.</p>
          ) : (
            <div className="space-y-5">
              <div className="grid place-items-center">
                <ScoreRing score={result.match_score} size={140} label="Match Score" />
              </div>
              {result.recommendation && <p className="text-sm bg-muted p-3 rounded-md italic">{result.recommendation}</p>}
              <div>
                <h3 className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Matched skills</h3>
                <div className="flex flex-wrap gap-1.5">
                  {matched.map((s) => <span key={s} className="text-xs px-2 py-1 rounded-md bg-success/15 text-success">{s}</span>)}
                </div>
              </div>
              <div>
                <h3 className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Skill gaps</h3>
                <div className="flex flex-wrap gap-1.5">
                  {missing.map((s) => <span key={s} className="text-xs px-2 py-1 rounded-md bg-destructive/10 text-destructive">{s}</span>)}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      <section className="mt-8 rounded-xl border border-border bg-card p-6 shadow-soft">
        <h2 className="font-semibold mb-4">Match history</h2>
        {matches.length === 0 ? (
          <p className="text-sm text-muted-foreground">No matches yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {matches.map((m) => (
              <li key={m.id} className="py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <div className="font-medium truncate">{m.job_descriptions?.title ?? "Job"} {m.job_descriptions?.company && <span className="text-muted-foreground">· {m.job_descriptions.company}</span>}</div>
                  <div className="text-xs text-muted-foreground truncate">{m.resumes?.title} · {new Date(m.created_at).toLocaleDateString()}</div>
                </div>
                <span className="text-sm font-bold">{m.match_score}%</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
