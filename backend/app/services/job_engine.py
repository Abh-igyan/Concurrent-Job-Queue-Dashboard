from __future__ import annotations

import logging
import queue
import random
import threading
import time
from datetime import datetime, timezone
from itertools import count
from typing import Any

from app.core.config import Settings
from app.models.job import Job, JobState, JobType, PRIORITY_ORDER, Priority, QueuedJob
from app.services.events import EventLog
from app.services.metrics import MetricsRegistry

logger = logging.getLogger(__name__)


class QueueFullError(RuntimeError):
    pass


class JobEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._queue: queue.PriorityQueue[QueuedJob] = queue.PriorityQueue(
            maxsize=settings.queue_capacity
        )
        self._shutdown = threading.Event()
        self._workers: list[threading.Thread] = []
        self._sequence = count()
        self._jobs: dict[str, Job] = {}
        self._jobs_lock = threading.RLock()
        self._timers: list[threading.Timer] = []
        self.metrics = MetricsRegistry(settings.worker_count)
        self.events = EventLog(settings.history_limit)

    def start(self) -> None:
        logger.info("starting job engine", extra={"worker_id": "all"})
        self._shutdown.clear()
        for worker_id in range(self.settings.worker_count):
            thread = threading.Thread(
                target=self._worker_loop,
                args=(worker_id,),
                name=f"job-worker-{worker_id}",
                daemon=False,
            )
            thread.start()
            self._workers.append(thread)
        self.events.append("engine_started", "worker pool started", {"workers": len(self._workers)})

    def shutdown(self) -> None:
        logger.info("shutting down job engine")
        self._shutdown.set()
        for timer in self._timers:
            timer.cancel()
        for thread in self._workers:
            thread.join(timeout=5)
        self.events.append("engine_stopped", "worker pool stopped", {})

    def submit(
        self,
        job_type: JobType,
        priority: Priority,
        duration_ms: int,
        max_retries: int | None = None,
        failure_rate: float = 0.05,
        payload: dict[str, Any] | None = None,
    ) -> Job:
        job = Job(
            job_type=job_type,
            priority=priority,
            duration_ms=max(1, duration_ms),
            max_retries=self.settings.default_max_retries if max_retries is None else max_retries,
            failure_rate=max(0.0, min(failure_rate, 1.0)),
            payload=payload or {},
        )
        self._enqueue_job(job, block=True, timeout=self.settings.enqueue_timeout_seconds)
        return job

    def cancel(self, job_id: str) -> bool:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if job is None or job.state not in {JobState.QUEUED, JobState.RETRIED}:
                return False
            job.state = JobState.CANCELLED
            job.finished_at = datetime.now(timezone.utc)
        self.metrics.mark_cancelled()
        self.events.append("job_cancelled", "queued job cancelled", {"job_id": job_id})
        return True

    def snapshot(self) -> dict[str, Any]:
        with self._jobs_lock:
            active_jobs = [
                job.to_dict()
                for job in self._jobs.values()
                if job.state in {JobState.RUNNING, JobState.QUEUED, JobState.RETRIED}
            ][-100:]
        return self.metrics.snapshot(self._queue.qsize(), active_jobs)

    def recent_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._jobs_lock:
            jobs = sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)
            return [job.to_dict() for job in jobs[:limit]]

    def _enqueue_job(self, job: Job, block: bool, timeout: float | None) -> None:
        job.state = JobState.QUEUED
        job.queued_at = datetime.now(timezone.utc)
        queued = QueuedJob(PRIORITY_ORDER[job.priority], next(self._sequence), job)
        try:
            self._queue.put(queued, block=block, timeout=timeout)
        except queue.Full as exc:
            raise QueueFullError("bounded queue is full; producer experienced backpressure") from exc

        with self._jobs_lock:
            self._jobs[job.id] = job

        self.metrics.mark_submitted(self._queue.qsize())
        self.events.append(
            "job_queued",
            "job queued",
            {"job_id": job.id, "type": job.job_type.value, "priority": job.priority.value},
        )

    def _worker_loop(self, worker_id: int) -> None:
        while not self._shutdown.is_set():
            try:
                queued = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            job = queued.job
            if job.state == JobState.CANCELLED:
                self._queue.task_done()
                continue

            self._run_job(worker_id, job)
            self._queue.task_done()

    def _run_job(self, worker_id: int, job: Job) -> None:
        job.state = JobState.RUNNING
        job.worker_id = worker_id
        job.started_at = datetime.now(timezone.utc)
        job.attempts += 1
        self.metrics.mark_worker(worker_id, True, job.id)
        self.events.append("job_running", "job started", {"job_id": job.id, "worker_id": worker_id})

        try:
            self._execute(job)
            if random.random() < job.failure_rate:
                raise RuntimeError("simulated transient worker failure")
        except Exception as exc:
            self._handle_failure(job, exc)
        else:
            job.state = JobState.COMPLETED
            job.finished_at = datetime.now(timezone.utc)
            latency_ms = (job.finished_at - job.created_at).total_seconds() * 1000
            self.metrics.mark_completed(latency_ms)
            self.events.append(
                "job_completed",
                "job completed",
                {"job_id": job.id, "worker_id": worker_id, "latency_ms": round(latency_ms, 2)},
            )
        finally:
            self.metrics.mark_worker(worker_id, False, None)

    def _handle_failure(self, job: Job, exc: Exception) -> None:
        job.last_error = str(exc)
        if job.attempts <= job.max_retries:
            job.state = JobState.RETRIED
            self.metrics.mark_retried()
            self.events.append(
                "job_retried",
                "job scheduled for retry",
                {"job_id": job.id, "attempt": job.attempts, "error": str(exc)},
            )
            timer = threading.Timer(self.settings.retry_delay_seconds, self._retry_job, args=(job,))
            timer.daemon = True
            timer.start()
            self._timers.append(timer)
            return

        job.state = JobState.FAILED
        job.finished_at = datetime.now(timezone.utc)
        self.metrics.mark_failed()
        self.events.append(
            "job_failed",
            "job failed permanently",
            {"job_id": job.id, "attempts": job.attempts, "error": str(exc)},
        )

    def _retry_job(self, job: Job) -> None:
        if self._shutdown.is_set() or job.state == JobState.CANCELLED:
            return
        try:
            self._enqueue_job(job, block=True, timeout=self.settings.enqueue_timeout_seconds)
        except QueueFullError:
            self.events.append("retry_backpressure", "retry blocked by full queue", {"job_id": job.id})
            self._handle_failure(job, RuntimeError("retry enqueue timed out under backpressure"))

    @staticmethod
    def _execute(job: Job) -> None:
        duration_s = job.duration_ms / 1000.0
        if job.job_type == JobType.CPU:
            deadline = time.perf_counter() + duration_s
            value = 0
            while time.perf_counter() < deadline:
                value = ((value << 5) ^ (value >> 2) ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
            job.payload["checksum"] = value
        elif job.job_type == JobType.IO:
            time.sleep(duration_s)
        elif job.job_type == JobType.DELAYED:
            time.sleep(duration_s * 1.5)
        else:
            raise ValueError(f"unsupported job type: {job.job_type}")
