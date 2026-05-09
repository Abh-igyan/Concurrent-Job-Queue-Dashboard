export type JobState = "queued" | "running" | "completed" | "failed" | "retried" | "cancelled";

export interface Job {
  id: string;
  type: "cpu" | "io" | "delayed";
  priority: "high" | "normal" | "low";
  state: JobState;
  duration_ms: number;
  attempts: number;
  max_retries: number;
  failure_rate: number;
  worker_id: number | null;
  last_error: string | null;
}

export interface MetricsSnapshot {
  timestamp: string;
  queue_depth: number;
  throughput_jobs_sec: number;
  worker_utilization: number;
  busy_workers: number;
  worker_count: number;
  submitted: number;
  completed: number;
  failed: number;
  retried: number;
  cancelled: number;
  peak_queue_size: number;
  latency_avg_ms: number;
  latency_p95_ms: number;
  worker_current_job: Record<string, string | null>;
  active_jobs: Job[];
}

export interface EventRecord {
  type: string;
  message: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface SocketPayload {
  type: "metrics_snapshot";
  metrics: MetricsSnapshot;
  events: EventRecord[];
}

export interface SeriesPoint {
  time: string;
  queue: number;
  throughput: number;
  utilization: number;
  latencyP95: number;
}
