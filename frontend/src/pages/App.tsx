import { Activity, AlertTriangle, Gauge, ListTree, Radio, RotateCcw, Timer, Zap } from "lucide-react";
import { useState } from "react";
import { ActiveJobs } from "../components/ActiveJobs";
import { QueueChart, ThroughputChart } from "../components/Charts";
import { EventLog } from "../components/EventLog";
import { MetricCard } from "../components/MetricCard";
import { WorkerGrid } from "../components/WorkerGrid";
import { createBurst, createJob } from "../lib/api";
import { useMetricsSocket } from "../lib/useMetricsSocket";

export function App() {
  const { metrics, events, series, connected } = useMetricsSocket();
  const [duration, setDuration] = useState(250);
  const [burst, setBurst] = useState(32);

  async function submitBurst() {
    await createBurst(burst, duration);
  }

  async function submitPriorityJob() {
    await createJob("cpu", "high", duration);
  }

  return (
    <main className="grid-bg min-h-screen">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <span className="rounded-sm border border-accent/30 bg-accent/10 px-2 py-1 font-mono text-xs text-accent">
                queue-runtime
              </span>
              <span className="flex items-center gap-2 font-mono text-xs text-slate-500">
                <Radio size={14} className={connected ? "text-ok" : "text-danger"} />
                {connected ? "websocket live" : "disconnected"}
              </span>
            </div>
            <h1 className="text-2xl font-semibold text-slate-100 sm:text-3xl">
              Concurrent Job Queue Dashboard
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">
              Bounded queue pressure, worker saturation, retries, throughput, and latency from a live threaded backend engine.
            </p>
          </div>

          <div className="flex flex-wrap items-end gap-3 rounded-md border border-border bg-panel/90 p-3">
            <label className="grid gap-1 text-xs uppercase tracking-wider text-slate-500">
              Burst
              <input
                className="w-24 rounded-md border border-border bg-slate-950 px-3 py-2 font-mono text-sm text-slate-200"
                type="number"
                min={1}
                max={500}
                value={burst}
                onChange={(event) => setBurst(Number(event.target.value))}
              />
            </label>
            <label className="grid gap-1 text-xs uppercase tracking-wider text-slate-500">
              Duration ms
              <input
                className="w-32 rounded-md border border-border bg-slate-950 px-3 py-2 font-mono text-sm text-slate-200"
                type="number"
                min={1}
                max={30000}
                value={duration}
                onChange={(event) => setDuration(Number(event.target.value))}
              />
            </label>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-accent/40 bg-accent/10 px-4 py-2 text-sm font-medium text-accent hover:bg-accent/20"
              onClick={submitBurst}
            >
              <Zap size={16} />
              Burst
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-warn/40 bg-warn/10 px-4 py-2 text-sm font-medium text-warn hover:bg-warn/20"
              onClick={submitPriorityJob}
            >
              <ListTree size={16} />
              High priority
            </button>
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Queue depth"
            value={String(metrics.queue_depth)}
            detail={`Peak observed ${metrics.peak_queue_size}`}
            icon={<Gauge size={20} />}
            tone={metrics.queue_depth > metrics.worker_count * 2 ? "warn" : "normal"}
          />
          <MetricCard
            label="Throughput"
            value={`${metrics.throughput_jobs_sec.toFixed(2)}/s`}
            detail={`${metrics.completed} completed of ${metrics.submitted} submitted`}
            icon={<Activity size={20} />}
            tone="ok"
          />
          <MetricCard
            label="Worker utilization"
            value={`${(metrics.worker_utilization * 100).toFixed(0)}%`}
            detail={`${metrics.busy_workers}/${metrics.worker_count} workers running`}
            icon={<Timer size={20} />}
            tone={metrics.worker_utilization > 0.85 ? "warn" : "normal"}
          />
          <MetricCard
            label="Retries / failures"
            value={`${metrics.retried}/${metrics.failed}`}
            detail={`cancelled ${metrics.cancelled}, p95 ${metrics.latency_p95_ms.toFixed(1)}ms`}
            icon={metrics.failed > 0 ? <AlertTriangle size={20} /> : <RotateCcw size={20} />}
            tone={metrics.failed > 0 ? "danger" : "warn"}
          />
        </section>

        <section className="mt-4 grid gap-4 lg:grid-cols-2">
          <QueueChart data={series} />
          <ThroughputChart data={series} />
        </section>

        <section className="mt-4">
          <WorkerGrid metrics={metrics} />
        </section>

        <section className="mt-4 grid gap-4 xl:grid-cols-[1fr_420px]">
          <ActiveJobs jobs={metrics.active_jobs} />
          <EventLog events={events} />
        </section>
      </div>
    </main>
  );
}
