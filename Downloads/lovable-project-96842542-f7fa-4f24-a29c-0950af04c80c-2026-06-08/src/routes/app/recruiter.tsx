import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCandidates, getMyRole, setMyRole } from "@/lib/data.functions";
import { rankCandidatesForJD } from "@/lib/ranking.functions";
import {
  Users,
  ShieldCheck,
  Sparkles,
  Loader2,
  Trophy,
  Building2,
  DoorOpen,
  Milestone,
  ArrowLeft,
  ArrowRight,
  Check,
} from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/app/recruiter")({ component: Recruiter });

type Filters = {
  seniority: string;
  mustHaveSkills: string;
  niceToHaveSkills: string;
  minYears: number;
  workMode: string;
  domain: string;
  cultureNotes: string;
};

const EMPTY_FILTERS: Filters = {
  seniority: "",
  mustHaveSkills: "",
  niceToHaveSkills: "",
  minYears: 0,
  workMode: "",
  domain: "",
  cultureNotes: "",
};

function Recruiter() {
  const qc = useQueryClient();

  const { data: role } = useQuery({ queryKey: ["my-role"], queryFn: getMyRole });
  const { data: candidates = [] } = useQuery({
    queryKey: ["candidates"],
    queryFn: listCandidates,
    enabled: !!role?.isRecruiter,
  });

  const enable = useMutation({
    mutationFn: () => setMyRole({ role: "recruiter" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-role"] });
      toast.success("Recruiter access enabled");
    },
  });

  // Wizard + filters
  const [step, setStep] = useState(0); // 0..5
  const [jdTitle, setJdTitle] = useState("");
  const [jdText, setJdText] = useState("");
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [topN, setTopN] = useState<number>(5);

  type Ranked = Awaited<ReturnType<typeof rankCandidatesForJD>>;
  const [ranked, setRanked] = useState<Ranked | null>(null);

  // Drilldown: "street" (overview) | "building" (top-N list) | "room" (single candidate)
  const [view, setView] = useState<"street" | "building" | "room">("street");
  const [activeId, setActiveId] = useState<string | null>(null);

  const rank = useMutation({
    mutationFn: () => rankCandidatesForJD({ jdTitle, jdText, filters, limit: 50 }),
    onSuccess: (r) => {
      setRanked(r);
      setView("street");
      toast.success(`Ranked ${r.length} candidates`);
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Ranking failed"),
  });

  const topList = useMemo(() => (ranked ? ranked.slice(0, topN) : []), [ranked, topN]);
  const activeCandidate = useMemo(
    () => topList.find((r) => r.resume_id === activeId) ?? null,
    [topList, activeId],
  );

  if (!role?.isRecruiter) {
    const features = [
      { icon: Users, title: "Full candidate pool", desc: "Browse every analyzed resume across the platform." },
      { icon: Sparkles, title: "AI job matching", desc: "Paste a JD, answer 5 quick questions, get a ranked shortlist." },
      { icon: Trophy, title: "Street → Building → Room", desc: "Drill from skyline overview into each candidate's room." },
    ];
    return (
      <div className="p-6 md:p-10 max-w-3xl mx-auto">
        <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-8 md:p-10 shadow-elegant">
          <div className="absolute inset-x-0 -top-24 h-48 bg-gradient-primary opacity-20 blur-3xl pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-3 mb-2">
              <div className="grid place-items-center size-12 rounded-xl bg-gradient-primary text-primary-foreground shadow-elegant">
                <ShieldCheck className="size-6" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">Recruiter access</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Unlock the recruiter dashboard</h1>
            <p className="text-muted-foreground mt-2 max-w-xl">
              Switch on recruiter mode to unlock guided filtering and an architectural drill-down view of your shortlist.
            </p>

            <div className="grid sm:grid-cols-3 gap-3 mt-6">
              {features.map((f) => (
                <div key={f.title} className="rounded-lg border border-border bg-background/50 p-4">
                  <f.icon className="size-5 text-primary mb-2" />
                  <div className="font-medium text-sm">{f.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{f.desc}</div>
                </div>
              ))}
            </div>

            <div className="mt-7 flex flex-wrap items-center gap-3">
              <button
                onClick={() => enable.mutate()}
                disabled={enable.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-6 py-3 text-sm font-semibold shadow-elegant hover:opacity-95 transition disabled:opacity-50"
              >
                {enable.isPending ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Enabling…
                  </>
                ) : (
                  <>
                    <ShieldCheck className="size-4" /> Enable Recruiter Mode
                  </>
                )}
              </button>
              <span className="text-xs text-muted-foreground">Free • Reversible from your profile</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function exportCsv() {
    if (!topList || topList.length === 0) return;
    const headers = ["Rank", "Candidate", "Combined", "Match", "ATS", "Health", "Matched", "Missing", "Reason"];
    const rows = topList.map((r, i) => [
      String(i + 1),
      r.title,
      String(r.combined_score),
      String(r.match_score),
      String(r.ats_score),
      String(r.health_score),
      r.matched_skills.join("; "),
      r.missing_skills.join("; "),
      r.reason,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shortlist-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // --- Wizard steps ---
  const steps = [
    {
      key: "jd",
      title: "The Brief",
      hint: "Paste the role you're hiring for.",
      valid: () => jdTitle.trim().length > 0 && jdText.trim().length >= 20,
      body: (
        <div className="space-y-3">
          <input
            value={jdTitle}
            onChange={(e) => setJdTitle(e.target.value)}
            placeholder="Job title (e.g. Senior React Engineer)"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            rows={6}
            placeholder="Paste the job description here…"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
      ),
    },
    {
      key: "seniority",
      title: "Seniority & Experience",
      hint: "Who are you actually looking for?",
      valid: () => true,
      body: (
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Seniority</span>
            <select
              value={filters.seniority}
              onChange={(e) => setFilters((s) => ({ ...s, seniority: e.target.value }))}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Any</option>
              <option>Intern</option>
              <option>Junior (0–2 yrs)</option>
              <option>Mid (2–5 yrs)</option>
              <option>Senior (5–8 yrs)</option>
              <option>Staff / Lead (8+ yrs)</option>
              <option>Principal / Manager</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Min years of relevant experience: <b>{filters.minYears}</b></span>
            <input
              type="range"
              min={0}
              max={15}
              value={filters.minYears}
              onChange={(e) => setFilters((s) => ({ ...s, minYears: Number(e.target.value) }))}
              className="w-full"
            />
          </label>
        </div>
      ),
    },
    {
      key: "skills",
      title: "Skills",
      hint: "What's non-negotiable vs nice to have?",
      valid: () => true,
      body: (
        <div className="space-y-3">
          <label className="block text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Must-have skills (comma separated)</span>
            <input
              value={filters.mustHaveSkills}
              onChange={(e) => setFilters((s) => ({ ...s, mustHaveSkills: e.target.value }))}
              placeholder="React, TypeScript, REST APIs"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Nice-to-have skills</span>
            <input
              value={filters.niceToHaveSkills}
              onChange={(e) => setFilters((s) => ({ ...s, niceToHaveSkills: e.target.value }))}
              placeholder="GraphQL, AWS, Design systems"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </label>
        </div>
      ),
    },
    {
      key: "context",
      title: "Context & Culture",
      hint: "Where, what domain, what team vibe?",
      valid: () => true,
      body: (
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Work mode</span>
            <select
              value={filters.workMode}
              onChange={(e) => setFilters((s) => ({ ...s, workMode: e.target.value }))}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Any</option>
              <option>Remote</option>
              <option>Hybrid</option>
              <option>On-site</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Domain / industry</span>
            <input
              value={filters.domain}
              onChange={(e) => setFilters((s) => ({ ...s, domain: e.target.value }))}
              placeholder="Fintech, Healthtech, B2B SaaS…"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </label>
          <label className="sm:col-span-2 text-sm">
            <span className="block text-xs text-muted-foreground mb-1">Team / culture notes</span>
            <textarea
              value={filters.cultureNotes}
              onChange={(e) => setFilters((s) => ({ ...s, cultureNotes: e.target.value }))}
              rows={3}
              placeholder="Small team, ships fast, strong product sense, mentors juniors…"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </label>
        </div>
      ),
    },
    {
      key: "topn",
      title: "Shortlist size",
      hint: "How many top profiles do you want surfaced?",
      valid: () => topN >= 1 && topN <= 50,
      body: (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={50}
              value={topN}
              onChange={(e) => setTopN(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
              className="w-28 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <span className="text-sm text-muted-foreground">top profiles (1–50)</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {[3, 5, 10, 15, 20, 25].map((n) => (
              <button
                key={n}
                onClick={() => setTopN(n)}
                className={`rounded-full border px-3 py-1 text-xs transition ${
                  topN === n
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border bg-background hover:bg-muted"
                }`}
              >
                Top {n}
              </button>
            ))}
          </div>
        </div>
      ),
    },
  ] as const;

  const cur = steps[step];
  const lastStep = step === steps.length - 1;

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Recruiter Studio</h1>
        <p className="text-muted-foreground mt-1">
          Guided filtering, then drill from the skyline into each candidate's room.
        </p>
      </header>

      {/* Wizard */}
      <section className="mb-8 rounded-xl border border-border bg-card p-6 shadow-soft">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-5">
          {steps.map((s, i) => (
            <div key={s.key} className="flex items-center gap-2 flex-1">
              <div
                className={`flex size-7 items-center justify-center rounded-full text-xs font-bold transition ${
                  i < step
                    ? "bg-primary text-primary-foreground"
                    : i === step
                      ? "bg-gradient-primary text-primary-foreground shadow-elegant"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {i < step ? <Check className="size-3.5" /> : i + 1}
              </div>
              {i < steps.length - 1 && (
                <div className={`h-px flex-1 ${i < step ? "bg-primary" : "bg-border"}`} />
              )}
            </div>
          ))}
        </div>

        <div className="mb-4">
          <h2 className="font-semibold text-lg">{cur.title}</h2>
          <p className="text-xs text-muted-foreground">{cur.hint}</p>
        </div>

        <div>{cur.body}</div>

        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium disabled:opacity-40"
          >
            <ArrowLeft className="size-4" /> Back
          </button>
          {!lastStep ? (
            <button
              onClick={() => cur.valid() && setStep((s) => s + 1)}
              disabled={!cur.valid()}
              className="inline-flex items-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-5 py-2 text-sm font-semibold shadow-elegant disabled:opacity-50"
            >
              Next <ArrowRight className="size-4" />
            </button>
          ) : (
            <button
              onClick={() => rank.mutate()}
              disabled={rank.isPending || !steps[0].valid()}
              className="inline-flex items-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-5 py-2 text-sm font-semibold shadow-elegant disabled:opacity-50"
            >
              {rank.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Ranking…
                </>
              ) : (
                <>
                  <Sparkles className="size-4" /> Rank candidates
                </>
              )}
            </button>
          )}
        </div>
      </section>

      {/* Architectural drill-down */}
      {ranked && ranked.length > 0 && (
        <section className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
          {/* Breadcrumb */}
          <div className="px-4 py-3 border-b border-border flex items-center justify-between gap-2 flex-wrap">
            <nav className="flex items-center gap-2 text-xs">
              <button
                onClick={() => {
                  setView("street");
                  setActiveId(null);
                }}
                className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${view === "street" ? "bg-primary/10 text-primary font-semibold" : "text-muted-foreground hover:bg-muted"}`}
              >
                <Milestone className="size-3.5" /> Street
              </button>
              <span className="text-muted-foreground">/</span>
              <button
                onClick={() => view !== "street" && setView("building")}
                disabled={view === "street"}
                className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${view === "building" ? "bg-primary/10 text-primary font-semibold" : "text-muted-foreground hover:bg-muted disabled:opacity-40"}`}
              >
                <Building2 className="size-3.5" /> Building
              </button>
              <span className="text-muted-foreground">/</span>
              <button
                disabled={view !== "room"}
                className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${view === "room" ? "bg-primary/10 text-primary font-semibold" : "text-muted-foreground disabled:opacity-40"}`}
              >
                <DoorOpen className="size-3.5" /> Room
              </button>
            </nav>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{topList.length} of {ranked.length} surfaced</span>
              <button
                onClick={exportCsv}
                className="rounded-md border border-border bg-background px-3 py-1 text-xs font-medium"
              >
                Export CSV
              </button>
            </div>
          </div>

          {/* STREET — skyline of buildings */}
          {view === "street" && (
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Milestone className="size-4 text-primary" />
                <h3 className="font-semibold text-sm">The Street — top {topList.length} candidates as a skyline</h3>
              </div>
              <p className="text-xs text-muted-foreground mb-6">
                Each building's height reflects combined score. Click a building to step inside.
              </p>

              <div className="relative h-72 rounded-lg border border-border bg-gradient-to-b from-background to-muted/40 overflow-hidden">
                {/* sky glow */}
                <div className="absolute inset-x-0 top-0 h-24 bg-gradient-primary opacity-10 blur-2xl pointer-events-none" />
                {/* ground */}
                <div className="absolute inset-x-0 bottom-0 h-2 bg-border" />
                <div className="absolute inset-x-0 bottom-2 flex items-end justify-around gap-2 px-4 pb-0 h-[calc(100%-0.5rem)]">
                  {topList.map((r, i) => {
                    const h = Math.max(20, r.combined_score); // % of available height
                    const isTop = i === 0;
                    return (
                      <button
                        key={r.resume_id}
                        onClick={() => {
                          setActiveId(r.resume_id);
                          setView("building");
                        }}
                        className="group relative flex-1 max-w-[90px] flex flex-col items-center justify-end transition"
                        style={{ height: "100%" }}
                        title={r.title}
                      >
                        <div className="text-[10px] font-bold text-muted-foreground mb-1 group-hover:text-foreground">
                          {r.combined_score}
                        </div>
                        <div
                          className={`w-full rounded-t-md border border-b-0 border-border transition-all group-hover:opacity-100 ${
                            isTop
                              ? "bg-gradient-primary shadow-elegant"
                              : "bg-primary/30 group-hover:bg-primary/60"
                          }`}
                          style={{ height: `${h}%` }}
                        >
                          {/* windows */}
                          <div className="h-full w-full p-1 grid grid-cols-2 gap-1 content-start opacity-80">
                            {Array.from({ length: Math.min(10, Math.floor(h / 8)) }).map((_, k) => (
                              <div key={k} className="h-1.5 rounded-sm bg-primary-foreground/40" />
                            ))}
                          </div>
                        </div>
                        <div className="mt-1 w-full truncate text-[10px] text-muted-foreground group-hover:text-foreground">
                          #{i + 1}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* mini legend list */}
              <ol className="mt-6 grid sm:grid-cols-2 gap-2">
                {topList.map((r, i) => (
                  <li key={r.resume_id}>
                    <button
                      onClick={() => {
                        setActiveId(r.resume_id);
                        setView("building");
                      }}
                      className="w-full flex items-center gap-3 rounded-lg border border-border bg-background/50 hover:bg-muted/60 p-3 text-left transition"
                    >
                      <div
                        className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                          i === 0 ? "bg-gradient-primary text-primary-foreground" : "bg-muted"
                        }`}
                      >
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{r.title}</div>
                        <div className="text-xs text-muted-foreground truncate">{r.reason}</div>
                      </div>
                      <span className="rounded-md bg-primary/10 px-2 py-1 text-xs font-bold text-primary">
                        {r.combined_score}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* BUILDING — floors view of the active candidate */}
          {view === "building" && activeCandidate && (
            <div className="p-6">
              <div className="flex items-center justify-between gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <Building2 className="size-4 text-primary" />
                  <h3 className="font-semibold text-sm">
                    Building · {activeCandidate.title}
                  </h3>
                </div>
                <button
                  onClick={() => setView("street")}
                  className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
                >
                  <ArrowLeft className="size-3.5" /> back to street
                </button>
              </div>

              <p className="text-xs text-muted-foreground mb-4">
                Each floor is a dimension of fit. Open the door to enter the room.
              </p>

              <div className="grid md:grid-cols-[1fr,1.2fr] gap-6">
                {/* Building silhouette with floors */}
                <div className="relative rounded-xl border border-border bg-gradient-to-b from-muted/40 to-background overflow-hidden">
                  <div className="p-4 space-y-2">
                    {[
                      { label: "Combined fit", val: activeCandidate.combined_score },
                      { label: "JD match", val: activeCandidate.match_score },
                      { label: "ATS score", val: activeCandidate.ats_score },
                      { label: "Resume health", val: activeCandidate.health_score },
                    ].map((f, idx) => (
                      <div
                        key={f.label}
                        className={`relative rounded-md border border-border p-3 ${
                          idx === 0 ? "bg-gradient-primary text-primary-foreground" : "bg-background"
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className={idx === 0 ? "opacity-90" : "text-muted-foreground"}>{f.label}</span>
                          <span className="font-bold">{f.val}</span>
                        </div>
                        <div className={`mt-2 h-1.5 rounded-full overflow-hidden ${idx === 0 ? "bg-primary-foreground/20" : "bg-muted"}`}>
                          <div
                            className={`h-full ${idx === 0 ? "bg-primary-foreground" : "bg-primary"}`}
                            style={{ width: `${Math.max(2, Math.min(100, f.val))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="px-4 pb-4">
                    <button
                      onClick={() => setView("room")}
                      className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-4 py-2 text-sm font-semibold shadow-elegant"
                    >
                      <DoorOpen className="size-4" /> Enter the room
                    </button>
                  </div>
                </div>

                {/* Side: peers */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Other buildings on the street
                  </h4>
                  <ul className="space-y-1.5 max-h-[420px] overflow-auto pr-1">
                    {topList.map((r, i) => (
                      <li key={r.resume_id}>
                        <button
                          onClick={() => setActiveId(r.resume_id)}
                          className={`w-full flex items-center gap-3 rounded-md border p-2 text-left transition ${
                            r.resume_id === activeCandidate.resume_id
                              ? "border-primary bg-primary/5"
                              : "border-border hover:bg-muted/50"
                          }`}
                        >
                          <span className="flex size-6 items-center justify-center rounded-full bg-muted text-[11px] font-bold">
                            {i + 1}
                          </span>
                          <span className="flex-1 truncate text-sm">{r.title}</span>
                          <span className="text-xs font-bold text-primary">{r.combined_score}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* ROOM — full detail */}
          {view === "room" && activeCandidate && (
            <div className="p-6">
              <div className="flex items-center justify-between gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <DoorOpen className="size-4 text-primary" />
                  <h3 className="font-semibold text-sm">Room · {activeCandidate.title}</h3>
                </div>
                <button
                  onClick={() => setView("building")}
                  className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
                >
                  <ArrowLeft className="size-3.5" /> back to building
                </button>
              </div>

              <div className="rounded-xl border border-border bg-gradient-to-br from-background to-muted/30 p-6">
                <div className="flex flex-wrap items-center gap-3 mb-4">
                  <div className="grid place-items-center size-12 rounded-xl bg-gradient-primary text-primary-foreground shadow-elegant text-lg font-bold">
                    {activeCandidate.combined_score}
                  </div>
                  <div>
                    <div className="text-lg font-semibold">{activeCandidate.title}</div>
                    <div className="text-xs text-muted-foreground">{activeCandidate.reason}</div>
                  </div>
                </div>

                <div className="grid sm:grid-cols-3 gap-3 mb-5">
                  {[
                    { label: "JD match", val: activeCandidate.match_score },
                    { label: "ATS", val: activeCandidate.ats_score },
                    { label: "Health", val: activeCandidate.health_score },
                  ].map((m) => (
                    <div key={m.label} className="rounded-lg border border-border bg-background p-3">
                      <div className="text-xs text-muted-foreground">{m.label}</div>
                      <div className="text-xl font-bold">{m.val}</div>
                    </div>
                  ))}
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                      Matched skills
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {activeCandidate.matched_skills.length === 0 && (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                      {activeCandidate.matched_skills.map((s) => (
                        <span key={s} className="text-xs px-2 py-1 rounded bg-success/15 text-success">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                      Missing skills
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {activeCandidate.missing_skills.length === 0 && (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                      {activeCandidate.missing_skills.map((s) => (
                        <span key={s} className="text-xs px-2 py-1 rounded bg-destructive/10 text-destructive">
                          −{s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Full candidate pool (always available) */}
      {!ranked && (
        <div className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="font-semibold text-sm">All candidates ({candidates.length}) — ranked by ATS</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted text-muted-foreground">
                <tr>
                  <th className="text-left p-3 w-10">#</th>
                  <th className="text-left p-3">Candidate</th>
                  <th className="text-left p-3">Skills</th>
                  <th className="text-right p-3">ATS</th>
                  <th className="text-right p-3">Health</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-muted-foreground">
                      No candidates yet.
                    </td>
                  </tr>
                ) : (
                  candidates.map((c, i) => {
                    const skills = (c.skills as string[] | null) ?? [];
                    return (
                      <tr key={c.id} className="border-t border-border">
                        <td className="p-3 font-semibold text-muted-foreground">{i + 1}</td>
                        <td className="p-3">
                          <div className="font-medium">{c.title}</div>
                          <div className="text-xs text-muted-foreground line-clamp-1">{c.summary}</div>
                        </td>
                        <td className="p-3">
                          <div className="flex flex-wrap gap-1">
                            {skills.slice(0, 5).map((s) => (
                              <span key={s} className="text-xs px-2 py-0.5 rounded bg-accent text-accent-foreground">
                                {s}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="p-3 text-right font-bold">{c.ats_score ?? "—"}</td>
                        <td className="p-3 text-right">{c.health_score ?? "—"}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
