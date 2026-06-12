import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, FileText, Target, MessageSquare, Users, Sparkles, CheckCircle2 } from "lucide-react";
import heroImg from "@/assets/hero.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ResumeScout — AI Resume Analyzer & Recruiter Platform" },
      { name: "description", content: "Score resumes against ATS, match candidates with job descriptions, and hire faster with AI." },
    ],
  }),
  component: Landing,
});

const features = [
  { icon: FileText, title: "ATS Resume Scoring", desc: "Get an instant 0–100 health score and actionable suggestions." },
  { icon: Target, title: "JD Match Engine", desc: "AI semantic matching between resumes and job descriptions." },
  { icon: MessageSquare, title: "AI Career Assistant", desc: "Chat with your resume — rewrite bullets, prep interviews." },
  { icon: Users, title: "Recruiter Dashboard", desc: "Rank candidates by score, shortlist, and export." },
];

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/60 sticky top-0 bg-background/80 backdrop-blur-md z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-gradient-primary grid place-items-center shadow-elegant">
              <Sparkles className="size-4 text-primary-foreground" />
            </div>
            <span className="font-semibold tracking-tight">ResumeScout</span>
          </Link>
          <nav className="flex items-center gap-3">
            <Link to="/auth" className="text-sm text-muted-foreground hover:text-foreground">Sign in</Link>
            <Link to="/auth" className="text-sm font-medium rounded-md bg-foreground text-background px-4 py-2 hover:opacity-90">Get started</Link>
          </nav>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-accent text-accent-foreground px-3 py-1 text-xs font-medium mb-6">
            <Sparkles className="size-3" /> Powered by AI
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-[1.05]">
            Analyze resumes.<br />
            <span className="text-gradient">Hire smarter.</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-md">
            ResumeScout uses AI to score resumes against ATS standards, match candidates with job descriptions, and turn hiring into a 60-second decision.
          </p>
          <div className="mt-8 flex gap-3">
            <Link to="/auth" className="inline-flex items-center gap-2 rounded-md bg-gradient-primary text-primary-foreground px-5 py-3 text-sm font-medium shadow-elegant hover:opacity-95">
              Start free <ArrowRight className="size-4" />
            </Link>
            <a href="#features" className="inline-flex items-center rounded-md border border-border px-5 py-3 text-sm font-medium hover:bg-accent">
              Learn more
            </a>
          </div>
          <div className="mt-8 flex items-center gap-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="size-4 text-success" /> Free tier</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="size-4 text-success" /> No credit card</span>
          </div>
        </div>
        <div className="relative">
          <div className="absolute -inset-8 bg-gradient-primary opacity-20 blur-3xl rounded-full" />
          <img src={heroImg} alt="AI resume analysis" width={1536} height={1024} className="relative rounded-2xl shadow-lift border border-border/60" />
        </div>
      </section>

      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Everything you need to win hiring</h2>
          <p className="mt-3 text-muted-foreground">For job seekers and recruiters alike.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-xl border border-border bg-card shadow-soft hover:shadow-lift transition-shadow">
              <div className="size-10 rounded-lg bg-accent grid place-items-center mb-4">
                <f.icon className="size-5 text-accent-foreground" />
              </div>
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <div className="p-12 rounded-2xl bg-gradient-primary text-primary-foreground shadow-elegant">
          <h2 className="text-3xl md:text-4xl font-bold">Ready to scout your next hire?</h2>
          <p className="mt-3 opacity-90">Join hundreds analyzing resumes with AI today.</p>
          <Link to="/auth" className="mt-6 inline-flex items-center gap-2 rounded-md bg-background text-foreground px-5 py-3 text-sm font-medium hover:opacity-95">
            Get started free <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-border/60 py-8 text-center text-sm text-muted-foreground">
        © 2026 ResumeScout. Built with AI.
      </footer>
    </div>
  );
}
