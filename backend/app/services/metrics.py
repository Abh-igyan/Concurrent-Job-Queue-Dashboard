from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from threading import Lock
from typing import Any


@dataclass
class MetricsState:
    submitted: int = 0
    completed: int = 0
    failed: int = 0
    retried: int = 0
    cancelled: int = 0
    peak_queue_size: int = 0
    latencies_ms: deque[float] = field(default_factory=lambda: deque(maxlen=2048))
    worker_busy: dict[int, bool] = field(default_factory=dict)
    worker_current_job: dict[int, str | None] = field(default_factory=dict)
    last_completed: int = 0
    last_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsRegistry:
    def __init__(self, worker_count: int) -> None:
        self._lock = Lock()
        self._state = MetricsState(
            worker_busy={worker_id: False for worker_id in range(worker_count)},
            worker_current_job={worker_id: None for worker_id in range(worker_count)},
        )

    def mark_submitted(self, queue_size: int) -> None:
        with self._lock:
            self._state.submitted += 1
            self._state.peak_queue_size = max(self._state.peak_queue_size, queue_size)

    def mark_worker(self, worker_id: int, busy: bool, job_id: str | None = None) -> None:
        with self._lock:
            self._state.worker_busy[worker_id] = busy
            self._state.worker_current_job[worker_id] = job_id

    def mark_completed(self, latency_ms: float) -> None:
        with self._lock:
            self._state.completed += 1
            self._state.latencies_ms.append(latency_ms)

    def mark_failed(self) -> None:
        with self._lock:
            self._state.failed += 1

    def mark_retried(self) -> None:
        with self._lock:
            self._state.retried += 1

    def mark_cancelled(self) -> None:
        with self._lock:
            self._state.cancelled += 1

    def snapshot(self, queue_depth: int, active_jobs: list[dict[str, Any]]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self._lock:
            elapsed = max((now - self._state.last_timestamp).total_seconds(), 0.001)
            completed_delta = self._state.completed - self._state.last_completed
            throughput = completed_delta / elapsed
            self._state.last_completed = self._state.completed
            self._state.last_timestamp = now

            latencies = list(self._state.latencies_ms)
            latencies_sorted = sorted(latencies)
            p95 = 0.0
            if latencies_sorted:
                index = min(int(len(latencies_sorted) * 0.95), len(latencies_sorted) - 1)
                p95 = latencies_sorted[index]

            busy_workers = sum(1 for busy in self._state.worker_busy.values() if busy)
            worker_count = max(len(self._state.worker_busy), 1)

            return {
                "timestamp": now.isoformat(),
                "queue_depth": queue_depth,
                "throughput_jobs_sec": throughput,
                "worker_utilization": busy_workers / worker_count,
                "busy_workers": busy_workers,
                "worker_count": worker_count,
                "submitted": self._state.submitted,
                "completed": self._state.completed,
                "failed": self._state.failed,
                "retried": self._state.retried,
                "cancelled": self._state.cancelled,
                "peak_queue_size": self._state.peak_queue_size,
                "latency_avg_ms": mean(latencies) if latencies else 0.0,
                "latency_p95_ms": p95,
                "worker_current_job": dict(self._state.worker_current_job),
                "active_jobs": active_jobs,
            }
