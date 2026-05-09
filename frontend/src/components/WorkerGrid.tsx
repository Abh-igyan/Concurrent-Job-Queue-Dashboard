import clsx from "clsx";
import type { MetricsSnapshot } from "../types/metrics";

export function WorkerGrid({ metrics }: { metrics: MetricsSnapshot }) {
  const workers = Array.from({ length: metrics.worker_count }, (_, index) => index);
  return (
    <section className="rounded-md border border-border bg-panel/90 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Worker lanes</h2>
        <span className="font-mono text-sm text-slate-400">
          {metrics.busy_workers}/{metrics.worker_count} busy
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {workers.map((worker) => {
          const jobId = metrics.worker_current_job[String(worker)];
          return (
            <div
              key={worker}
              className={clsx(
                "rounded-md border p-3",
                jobId
                  ? "border-ok/40 bg-ok/10"
                  : "border-border bg-slate-950/30"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-slate-300">w{worker}</span>
                <span
                  className={clsx(
                    "h-2 w-2 rounded-full",
                    jobId ? "bg-ok shadow-[0_0_16px_rgba(52,211,153,0.8)]" : "bg-slate-600"
                  )}
                />
              </div>
              <p className="mt-3 truncate font-mono text-xs text-slate-500">
                {jobId ? jobId.slice(0, 8) : "idle"}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
