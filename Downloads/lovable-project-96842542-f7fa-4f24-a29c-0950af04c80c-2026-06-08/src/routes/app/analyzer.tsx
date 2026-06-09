import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeResume } from "@/lib/ai.functions";
import { importResumeFromUrl } from "@/lib/import.functions";
import { listMyResumes, deleteResume } from "@/lib/data.functions";
import { extractPdfText } from "@/lib/pdf";
import { ScoreRing } from "@/components/ScoreRing";
import { Sparkles, Trash2, FileText, Loader2, Link2, Linkedin, FileUp } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/app/analyzer")({ component: Analyzer });

type Suggestion = { category: string; title: string; detail: string };
type AnalyzedResume = Awaited<ReturnType<typeof analyzeResume>>;

function Analyzer() {
  const qc = useQueryClient();

  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [url, setUrl] = useState("");
  const [current, setCurrent] = useState<AnalyzedResume | null>(null);

  const { data: resumes = [] } = useQuery({ queryKey: ["resumes"], queryFn: listMyResumes });

  const mut = useMutation({
    mutationFn: (input: { title: string; rawText: string }) => analyzeResume(input),
    onSuccess: (r) => {
      setCurrent(r);
      qc.invalidateQueries({ queryKey: ["resumes"] });
      toast.success("Resume analyzed!");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Analysis failed"),
  });

  const del = useMutation({
    mutationFn: (id: string) => deleteResume({ id }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["resumes"] }); toast.success("Deleted"); },
  });

  const importMut = useMutation({
    mutationFn: (input: { url: string; title?: string }) => importResumeFromUrl(input),
    onSuccess: (r) => {
      setCurrent(r);
      qc.invalidateQueries({ queryKey: ["resumes"] });
      toast.success("Profile imported & analyzed!");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Import failed"),
  });

  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number } | null>(null);

  async function readFileText(f: File): Promise<string> {
    if (f.name.toLowerCase().endsWith(".pdf") || f.type === "application/pdf") {
      return await extractPdfText(f);
    }
    return await f.text();
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const text = await readFileText(f);
      setRawText(text);
      if (!title) setTitle(f.name.replace(/\.[^.]+$/, ""));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't read file");
    }
  }

  async function onBulkPdfs(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (files.length === 0) return;
    setBulkBusy(true);
    setBulkProgress({ done: 0, total: files.length });
    let ok = 0, fail = 0;
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      try {
        const text = await readFileText(f);
        if (text.length < 20) throw new Error("Empty PDF text");
        const r = await analyzeResume({ title: f.name.replace(/\.[^.]+$/, ""), rawText: text });
        setCurrent(r);
        ok++;
      } catch (err) {
        fail++;
        console.error(f.name, err);
      }
      setBulkProgress({ done: i + 1, total: files.length });
    }
    setBulkBusy(false);
    setBulkProgress(null);
    qc.invalidateQueries({ queryKey: ["resumes"] });
    toast.success(`Analyzed ${ok}/${files.length}${fail ? ` · ${fail} failed` : ""}`);
  }


  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <header className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Resume Analyzer</h1>
        <p className="text-muted-foreground mt-1">Paste, upload, or import from a public profile URL — AI scores it instantly.</p>
      </header>

      <section className="mb-6 rounded-xl border border-border bg-card p-5 shadow-soft">
        <div className="flex items-center gap-2 mb-3">
          <Linkedin className="size-4 text-primary" />
          <h2 className="font-semibold">Import from URL</h2>
          <span className="text-xs text-muted-foreground hidden sm:inline">· LinkedIn (public), Naukri, personal sites, GitHub</span>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 flex items-center gap-2 rounded-md border border-input bg-background px-3">
            <Link2 className="size-4 text-muted-foreground shrink-0" />
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.linkedin.com/in/username  or  https://www.naukri.com/…"
              className="flex-1 bg-transparent py-2 text-sm outline-none"
            />
          </div>
          <button
            onClick={() => importMut.mutate({ url, title: title || undefined })}
            disabled={importMut.isPending || !/^https?:\/\//i.test(url)}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-4 py-2 text-sm font-medium shadow-elegant disabled:opacity-50"
          >
            {importMut.isPending ? <><Loader2 className="size-4 animate-spin" /> Importing…</> : <>Import &amp; Analyze</>}
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Tip: LinkedIn blocks most private profiles. If import fails, copy the profile text and paste it below.
        </p>
      </section>


      <section className="mb-6 rounded-xl border border-border bg-card p-5 shadow-soft">
        <div className="flex items-center gap-2 mb-3">
          <FileUp className="size-4 text-primary" />
          <h2 className="font-semibold">Bulk PDF import</h2>
          <span className="text-xs text-muted-foreground hidden sm:inline">· Select one or many PDFs — each is analyzed and saved</span>
        </div>
        <label className="block">
          <input
            type="file"
            accept="application/pdf,.pdf"
            multiple
            onChange={onBulkPdfs}
            disabled={bulkBusy}
            className="block w-full text-sm file:mr-3 file:rounded-md file:border-0 file:bg-gradient-primary file:text-primary-foreground file:px-3 file:py-1.5 file:text-sm file:font-medium disabled:opacity-50"
          />
        </label>
        {bulkProgress && (
          <p className="text-xs text-muted-foreground mt-2 flex items-center gap-2">
            <Loader2 className="size-3 animate-spin" /> Analyzing {bulkProgress.done}/{bulkProgress.total}…
          </p>
        )}
      </section>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-semibold mb-4">New analysis</h2>
          <div className="space-y-3">
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title (e.g. Software Engineer Resume)" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            <label className="block">
              <span className="text-xs text-muted-foreground">Upload .pdf / .txt / .md (or paste below)</span>
              <input type="file" accept=".pdf,.txt,.md,.text,application/pdf" onChange={onFile} className="mt-1 block w-full text-sm file:mr-3 file:rounded-md file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-accent-foreground" />
            </label>
            <textarea value={rawText} onChange={(e) => setRawText(e.target.value)} rows={12} placeholder="Paste resume text here…" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" />
            <button
              onClick={() => mut.mutate({ title: title || "Untitled Resume", rawText })}
              disabled={mut.isPending || rawText.length < 20}
              className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-4 py-2.5 text-sm font-medium shadow-elegant disabled:opacity-50"
            >
              {mut.isPending ? <><Loader2 className="size-4 animate-spin" /> Analyzing…</> : <><Sparkles className="size-4" /> Analyze with AI</>}
            </button>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-semibold mb-4">Results</h2>
          {!current ? (
            <p className="text-sm text-muted-foreground">Run an analysis to see ATS score, skills, and suggestions.</p>
          ) : (
            <ResultsView resume={current} />
          )}
        </section>
      </div>

      <section className="mt-8 rounded-xl border border-border bg-card p-6 shadow-soft">
        <h2 className="font-semibold mb-4">Your resumes</h2>
        {resumes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No resumes yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {resumes.map((r) => (
              <li key={r.id} className="py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="size-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <div className="font-medium truncate">{r.title}</div>
                    <div className="text-xs text-muted-foreground truncate">{r.summary || "—"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-sm font-semibold">{r.ats_score ?? "—"}</span>
                  <button onClick={() => del.mutate(r.id)} className="text-muted-foreground hover:text-destructive"><Trash2 className="size-4" /></button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function ResultsView({ resume }: { resume: AnalyzedResume }) {
  const skills = (resume.skills as string[]) ?? [];
  const missing = (resume.missing_keywords as string[]) ?? [];
  const suggestions = (resume.suggestions as Suggestion[]) ?? [];
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-around">
        <ScoreRing score={resume.ats_score ?? 0} label="ATS Score" />
        <ScoreRing score={resume.health_score ?? 0} label="Health" />
      </div>
      {resume.summary && <p className="text-sm text-muted-foreground italic">{resume.summary}</p>}
      <div>
        <h3 className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Detected skills</h3>
        <div className="flex flex-wrap gap-1.5">
          {skills.map((s) => <span key={s} className="text-xs px-2 py-1 rounded-md bg-accent text-accent-foreground">{s}</span>)}
        </div>
      </div>
      {missing.length > 0 && (
        <div>
          <h3 className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Missing keywords</h3>
          <div className="flex flex-wrap gap-1.5">
            {missing.map((s) => <span key={s} className="text-xs px-2 py-1 rounded-md bg-destructive/10 text-destructive">{s}</span>)}
          </div>
        </div>
      )}
      {suggestions.length > 0 && (
        <div>
          <h3 className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Suggestions</h3>
          <ul className="space-y-2">
            {suggestions.map((s, i) => (
              <li key={i} className="p-3 rounded-md bg-muted">
                <div className="font-medium text-sm">{s.title}</div>
                <div className="text-xs text-muted-foreground mt-1">{s.detail}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
