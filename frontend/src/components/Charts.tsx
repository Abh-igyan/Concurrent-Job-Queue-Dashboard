import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { ReactNode } from "react";
import type { SeriesPoint } from "../types/metrics";

function ChartShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-border bg-panel/90 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">{title}</h2>
      </div>
      <div className="h-64">{children}</div>
    </section>
  );
}

export function QueueChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartShell title="Queue pressure">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="queue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4fd1c5" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#4fd1c5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#263142" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#10151f", border: "1px solid #263142" }} />
          <Area dataKey="queue" stroke="#4fd1c5" fill="url(#queue)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function ThroughputChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartShell title="Throughput and p95 latency">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#263142" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#10151f", border: "1px solid #263142" }} />
          <Line type="monotone" dataKey="throughput" stroke="#34d399" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="latencyP95" stroke="#fbbf24" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}
