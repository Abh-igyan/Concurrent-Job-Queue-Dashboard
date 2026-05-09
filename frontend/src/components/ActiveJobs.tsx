import clsx from "clsx";
import type { Job } from "../types/metrics";

export function ActiveJobs({ jobs }: { jobs: Job[] }) {
  return (
    <section className="rounded-md border border-border bg-panel/90 p-4">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-300">Active jobs</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="pb-3">Job</th>
              <th className="pb-3">Type</th>
              <th className="pb-3">Priority</th>
              <th className="pb-3">State</th>
              <th className="pb-3">Worker</th>
              <th className="pb-3">Attempt</th>
            </tr>
          </thead>
          <tbody>
            {jobs.slice(0, 12).map((job) => (
              <tr key={job.id} className="border-b border-border/60">
                <td className="py-3 font-mono text-xs text-slate-300">{job.id.slice(0, 12)}</td>
                <td className="py-3 text-slate-300">{job.type}</td>
                <td className="py-3 text-slate-300">{job.priority}</td>
                <td className="py-3">
                  <span
                    className={clsx(
                      "rounded-sm border px-2 py-1 text-xs",
                      job.state === "running" && "border-ok/40 bg-ok/10 text-ok",
                      job.state === "queued" && "border-accent/40 bg-accent/10 text-accent",
                      job.state === "retried" && "border-warn/40 bg-warn/10 text-warn"
                    )}
                  >
                    {job.state}
                  </span>
                </td>
                <td className="py-3 font-mono text-slate-400">{job.worker_id ?? "-"}</td>
                <td className="py-3 font-mono text-slate-400">
                  {job.attempts}/{job.max_retries}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {jobs.length === 0 && <p className="py-8 text-center text-sm text-slate-500">No active jobs</p>}
      </div>
    </section>
  );
}
