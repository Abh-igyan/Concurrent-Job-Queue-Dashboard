from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class JobType(str, Enum):
    CPU = "cpu"
    IO = "io"
    DELAYED = "delayed"


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


PRIORITY_ORDER = {
    Priority.HIGH: 0,
    Priority.NORMAL: 1,
    Priority.LOW: 2,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Job:
    job_type: JobType
    priority: Priority = Priority.NORMAL
    duration_ms: int = 250
    max_retries: int = 2
    failure_rate: float = 0.05
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.QUEUED
    attempts: int = 0
    created_at: datetime = field(default_factory=utc_now)
    queued_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_error: str | None = None
    worker_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.job_type.value,
            "priority": self.priority.value,
            "state": self.state.value,
            "duration_ms": self.duration_ms,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "failure_rate": self.failure_rate,
            "created_at": self.created_at.isoformat(),
            "queued_at": self.queued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "last_error": self.last_error,
            "worker_id": self.worker_id,
            "payload": self.payload,
        }


@dataclass(order=True)
class QueuedJob:
    priority_rank: int
    sequence: int
    job: Job = field(compare=False)
