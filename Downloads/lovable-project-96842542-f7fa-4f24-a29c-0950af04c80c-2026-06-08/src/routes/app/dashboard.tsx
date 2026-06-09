import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { listMyResumes, getMyMatches } from "@/lib/data.functions";
import { FileText, Target, Plus, TrendingUp } from "lucide-react";

export const Route = createFileRoute("/app/dashboard")({ component: Dashboard });

function Dashboard() {
  const { data: resumes = [] } = useQuery({ queryKey: ["resumes"], queryFn: listMyResumes });
  const { data: matches = [] } = useQuery({ queryKey: ["matches"], queryFn: getMyMatches });

  const avgAts = resumes.length ? Math.round(resumes.reduce((s, r) => s + (r.ats_score ?? 0), 0) / resumes.length) : 0;
  const bestMatch = matches.length ? Math.max(...matches.map((m) => m.match_score)) : 0;

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Your resume intelligence at a glance.</p>
      </header>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <Stat label="Resumes" value={resumes.length} icon={FileText} />
        <Stat label="Avg ATS Score" value={avgAts} icon={TrendingUp} suffix="/100" />
        <Stat label="Best Match" value={bestMatch} icon={Target} suffix="%" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Recent resumes</h2>
            <Link to="/app/analyzer" className="text-sm inline-flex items-center gap-1 text-primary hover:underline">
              <Plus className="size-4" /> New
            </Link>
          </div>
          {resumes.length === 0 ? (
            <p className="text-sm text-muted-foreground">No resumes yet. <Link to="/app/analyzer" className="text-primary hover:underline">Analyze one</Link>.</p>
          ) : (
            <ul className="divide-y divide-border">
              {resumes.slice(0, 5).map((r) => (
                <li key={r.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-medium truncate">{r.title}</div>
                    <div className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleDateString()}</div>
                  </div>
                  <ScorePill score={r.ats_score ?? 0} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Recent matches</h2>
            <Link to="/app/match" className="text-sm inline-flex items-center gap-1 text-primary hover:underline">
              <Plus className="size-4" /> New match
            </Link>
          </div>
          {matches.length === 0 ? (
            <p className="text-sm text-muted-foreground">No JD matches yet.</p>
          ) : (
            <ul className="divide-y divide-border">
              {matches.slice(0, 5).map((m) => (
                <li key={m.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-medium truncate">{m.job_descriptions?.title ?? "Job"}</div>
                    <div className="text-xs text-muted-foreground truncate">{m.resumes?.title}</div>
                  </div>
                  <ScorePill score={m.match_score} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value, icon: Icon, suffix }: { label: string; value: number; icon: React.ComponentType<{ className?: string }>; suffix?: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <Icon className="size-4 text-muted-foreground" />
      </div>
      <div className="mt-2 text-3xl font-bold">{value}<span className="text-base text-muted-foreground font-normal">{suffix}</span></div>
    </div>
  );
}

function ScorePill({ score }: { score: number }) {
  const color = score >= 80 ? "bg-success/15 text-success" : score >= 60 ? "bg-primary/15 text-primary" : score >= 40 ? "bg-warning/15 text-warning-foreground" : "bg-destructive/15 text-destructive";
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${color}`}>{score}</span>;
}
