export function ScoreRing({ score, size = 120, label }: { score: number; size?: number; label?: string }) {
  const s = Math.max(0, Math.min(100, score));
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (s / 100) * c;
  const color =
    s >= 80 ? "var(--color-success)" : s >= 60 ? "var(--color-primary)" : s >= 40 ? "var(--color-warning)" : "var(--color-destructive)";
  return (
    <div className="inline-flex flex-col items-center gap-2">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--color-muted)" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          fill="none"
          style={{ transition: "stroke-dashoffset 600ms ease" }}
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          transform={`rotate(90 ${size / 2} ${size / 2})`}
          className="fill-foreground font-bold"
          fontSize={size / 4}
        >
          {s}
        </text>
      </svg>
      {label && <div className="text-sm text-muted-foreground">{label}</div>}
    </div>
  );
}
