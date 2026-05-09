from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import jobs, metrics
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.job_engine import JobEngine
from app.services.websocket_manager import WebSocketManager

settings = get_settings()
configure_logging(settings.log_level)
engine = JobEngine(settings)
ws_manager = WebSocketManager()


async def metrics_publisher() -> None:
    while True:
        await ws_manager.broadcast(
            {
                "type": "metrics_snapshot",
                "metrics": engine.snapshot(),
                "events": engine.events.tail(25),
            }
        )
        await asyncio.sleep(settings.metrics_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine.start()
    publisher = asyncio.create_task(metrics_publisher())
    try:
        yield
    finally:
        publisher.cancel()
        engine.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs.router(engine), prefix="/api")
app.include_router(metrics.router(engine), prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/metrics")
async def metrics_socket(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "metrics_snapshot",
                "metrics": engine.snapshot(),
                "events": engine.events.tail(25),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
