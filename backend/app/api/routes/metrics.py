from __future__ import annotations

from fastapi import APIRouter, Response

from app.services.job_engine import JobEngine


def router(engine: JobEngine) -> APIRouter:
    api = APIRouter(tags=["metrics"])

    @api.get("/metrics")
    def metrics() -> dict:
        return engine.snapshot()

    @api.get("/events")
    def events(limit: int = 50) -> list[dict]:
        return engine.events.tail(limit=max(1, min(limit, 200)))

    @api.get("/prometheus")
    def prometheus() -> Response:
        snapshot = engine.snapshot()
        lines = [
            "# HELP cjqd_queue_depth Current bounded queue depth",
            "# TYPE cjqd_queue_depth gauge",
            f"cjqd_queue_depth {snapshot['queue_depth']}",
            "# HELP cjqd_worker_utilization Fraction of busy workers",
            "# TYPE cjqd_worker_utilization gauge",
            f"cjqd_worker_utilization {snapshot['worker_utilization']}",
            "# HELP cjqd_jobs_total Total jobs by state",
            "# TYPE cjqd_jobs_total counter",
            f"cjqd_jobs_total{{state=\"submitted\"}} {snapshot['submitted']}",
            f"cjqd_jobs_total{{state=\"completed\"}} {snapshot['completed']}",
            f"cjqd_jobs_total{{state=\"failed\"}} {snapshot['failed']}",
            f"cjqd_jobs_total{{state=\"retried\"}} {snapshot['retried']}",
            "# HELP cjqd_latency_p95_ms Rolling p95 latency in milliseconds",
            "# TYPE cjqd_latency_p95_ms gauge",
            f"cjqd_latency_p95_ms {snapshot['latency_p95_ms']}",
        ]
        return Response("\n".join(lines) + "\n", media_type="text/plain")

    return api
