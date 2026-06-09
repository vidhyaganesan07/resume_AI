import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { askAssistant } from "@/lib/ai.functions";
import { listMyResumes } from "@/lib/data.functions";
import { Send, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/app/assistant")({ component: Assistant });

type Msg = { role: "user" | "assistant"; content: string };

function Assistant() {
  const { data: resumes = [] } = useQuery({ queryKey: ["resumes"], queryFn: listMyResumes });

  const [resumeId, setResumeId] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);

  const mut = useMutation({
    mutationFn: (q: string) => askAssistant({ resumeId: resumeId || undefined, question: q }),
    onSuccess: (r) => setMessages((m) => [...m, { role: "assistant", content: r.answer }]),
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed"),
  });

  function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const q = input.trim();
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    mut.mutate(q);
  }

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto h-screen flex flex-col">
      <header className="mb-4">
        <h1 className="text-3xl font-bold tracking-tight">AI Career Assistant</h1>
        <p className="text-muted-foreground mt-1">Chat with AI about your resume, interviews, or career.</p>
      </header>

      <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} className="mb-4 rounded-md border border-input bg-background px-3 py-2 text-sm max-w-sm">
        <option value="">No resume context</option>
        {resumes.map((r) => <option key={r.id} value={r.id}>Use: {r.title}</option>)}
      </select>

      <div className="flex-1 overflow-y-auto space-y-4 rounded-xl border border-border bg-card p-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-12">
            <Sparkles className="size-8 mx-auto mb-2 text-primary" />
            <p className="text-sm">Ask me anything — "rewrite my summary", "what are common SWE interview questions", etc.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            {m.role === "user" ? (
              <div className="max-w-[80%] rounded-2xl bg-primary text-primary-foreground px-4 py-2 text-sm">{m.content}</div>
            ) : (
              <div className="text-sm whitespace-pre-wrap">{m.content}</div>
            )}
          </div>
        ))}
        {mut.isPending && <div className="text-sm text-muted-foreground inline-flex items-center gap-2"><Loader2 className="size-4 animate-spin" /> Thinking…</div>}
      </div>

      <form onSubmit={send} className="mt-4 flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask anything…" className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm" />
        <button type="submit" disabled={mut.isPending} className="rounded-md bg-gradient-primary text-primary-foreground px-4 py-2 text-sm font-medium shadow-elegant disabled:opacity-50">
          <Send className="size-4" />
        </button>
      </form>
    </div>
  );
}
