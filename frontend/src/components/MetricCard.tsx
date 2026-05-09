import type { ReactNode } from "react";
import clsx from "clsx";

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  icon: ReactNode;
  tone?: "normal" | "ok" | "warn" | "danger";
}

export function MetricCard({ label, value, detail, icon, tone = "normal" }: MetricCardProps) {
  return (
    <section className="rounded-md border border-border bg-panel/90 p-4 shadow-xl shadow-black/10">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-2 font-mono text-2xl font-semibold text-slate-100">{value}</p>
        </div>
        <div
          className={clsx(
            "rounded-md border p-2",
            tone === "ok" && "border-ok/30 bg-ok/10 text-ok",
            tone === "warn" && "border-warn/30 bg-warn/10 text-warn",
            tone === "danger" && "border-danger/30 bg-danger/10 text-danger",
            tone === "normal" && "border-accent/30 bg-accent/10 text-accent"
          )}
        >
          {icon}
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-400">{detail}</p>
    </section>
  );
}
