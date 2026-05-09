from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.job import JobType, Priority
from app.services.job_engine import JobEngine, QueueFullError


class JobCreateRequest(BaseModel):
    job_type: JobType = JobType.CPU
    priority: Priority = Priority.NORMAL
    duration_ms: int = Field(default=250, ge=1, le=30_000)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    failure_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)


def router(engine: JobEngine) -> APIRouter:
    api = APIRouter(prefix="/jobs", tags=["jobs"])

    @api.post("")
    def create_job(request: JobCreateRequest) -> dict[str, Any]:
        try:
            job = engine.submit(
                job_type=request.job_type,
                priority=request.priority,
                duration_ms=request.duration_ms,
                max_retries=request.max_retries,
                failure_rate=request.failure_rate,
                payload=request.payload,
            )
        except QueueFullError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return job.to_dict()

    @api.post("/burst")
    def create_burst(count: int = 32, duration_ms: int = 250) -> dict[str, Any]:
        created: list[str] = []
        for index in range(max(1, min(count, 500))):
            job_type = [JobType.CPU, JobType.IO, JobType.DELAYED][index % 3]
            priority = [Priority.HIGH, Priority.NORMAL, Priority.LOW][index % 3]
            try:
                created.append(
                    engine.submit(
                        job_type=job_type,
                        priority=priority,
                        duration_ms=duration_ms,
                        failure_rate=0.08,
                    ).id
                )
            except QueueFullError as exc:
                raise HTTPException(
                    status_code=429,
                    detail={"message": str(exc), "created": created},
                ) from exc
        return {"created": len(created), "job_ids": created}

    @api.get("")
    def list_jobs(limit: int = 100) -> list[dict[str, Any]]:
        return engine.recent_jobs(limit=max(1, min(limit, 500)))

    @api.post("/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, Any]:
        if not engine.cancel(job_id):
            raise HTTPException(status_code=409, detail="job is not cancellable")
        return {"cancelled": True, "job_id": job_id}

    return api
