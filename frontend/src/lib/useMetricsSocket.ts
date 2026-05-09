import { useEffect, useMemo, useState } from "react";
import type { EventRecord, MetricsSnapshot, SeriesPoint, SocketPayload } from "../types/metrics";

const initialMetrics: MetricsSnapshot = {
  timestamp: new Date().toISOString(),
  queue_depth: 0,
  throughput_jobs_sec: 0,
  worker_utilization: 0,
  busy_workers: 0,
  worker_count: 0,
  submitted: 0,
  completed: 0,
  failed: 0,
  retried: 0,
  cancelled: 0,
  peak_queue_size: 0,
  latency_avg_ms: 0,
  latency_p95_ms: 0,
  worker_current_job: {},
  active_jobs: []
};

export function useMetricsSocket() {
  const [metrics, setMetrics] = useState<MetricsSnapshot>(initialMetrics);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/metrics`);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (message) => {
      const payload = JSON.parse(message.data) as SocketPayload;
      if (payload.type !== "metrics_snapshot") return;

      setMetrics(payload.metrics);
      setEvents(payload.events.slice().reverse());
      setSeries((current) => {
        const point: SeriesPoint = {
          time: new Date(payload.metrics.timestamp).toLocaleTimeString(),
          queue: payload.metrics.queue_depth,
          throughput: Number(payload.metrics.throughput_jobs_sec.toFixed(2)),
          utilization: Number((payload.metrics.worker_utilization * 100).toFixed(1)),
          latencyP95: Number(payload.metrics.latency_p95_ms.toFixed(1))
        };
        return [...current.slice(-59), point];
      });
    };

    return () => socket.close();
  }, []);

  return useMemo(() => ({ metrics, events, series, connected }), [metrics, events, series, connected]);
}
