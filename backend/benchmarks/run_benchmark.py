from __future__ import annotations

import argparse
import json
import queue
import statistics
import threading
import time
from dataclasses import dataclass
from pathlib import Path


def cpu_work(duration_ms: int) -> int:
    deadline = time.perf_counter() + duration_ms / 1000
    value = 0
    while time.perf_counter() < deadline:
        value = ((value << 5) ^ (value >> 2) ^ 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    return value


@dataclass
class Workload:
    name: str
    duration_ms: int
    tasks: int


def run_serial(workload: Workload) -> float:
    start = time.perf_counter()
    for _ in range(workload.tasks):
        cpu_work(workload.duration_ms)
    return time.perf_counter() - start


def run_concurrent(workload: Workload, workers: int) -> tuple[float, list[float]]:
    tasks: queue.Queue[int] = queue.Queue(maxsize=max(16, workers * 4))
    latencies: list[float] = []
    latencies_lock = threading.Lock()

    def worker() -> None:
        while True:
            item = tasks.get()
            if item < 0:
                tasks.task_done()
                return
            started = time.perf_counter()
            cpu_work(workload.duration_ms)
            with latencies_lock:
                latencies.append((time.perf_counter() - started) * 1000)
            tasks.task_done()

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for thread in threads:
        thread.start()

    start = time.perf_counter()
    for index in range(workload.tasks):
        tasks.put(index)
    for _ in threads:
        tasks.put(-1)
    tasks.join()
    elapsed = time.perf_counter() - start

    for thread in threads:
        thread.join()

    return elapsed, latencies


def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrent job queue benchmark")
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--output", type=Path, default=Path("benchmark-report.json"))
    args = parser.parse_args()

    workloads = [
        Workload("small", 10, 200),
        Workload("medium", 50, 100),
        Workload("large", 150, 50),
    ]
    rows = []

    for workload in workloads:
        serial_s = run_serial(workload)
        for workers in range(1, args.max_workers + 1):
            concurrent_s, latencies = run_concurrent(workload, workers)
            rows.append(
                {
                    "workload": workload.name,
                    "workers": workers,
                    "tasks": workload.tasks,
                    "task_duration_ms": workload.duration_ms,
                    "serial_seconds": serial_s,
                    "concurrent_seconds": concurrent_s,
                    "speedup": serial_s / concurrent_s,
                    "throughput_jobs_sec": workload.tasks / concurrent_s,
                    "latency_avg_ms": statistics.mean(latencies) if latencies else 0,
                    "latency_p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                }
            )

    args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
