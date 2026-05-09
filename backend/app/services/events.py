from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass
class Event:
    event_type: str
    message: str
    payload: dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.event_type,
            "message": self.message,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class EventLog:
    def __init__(self, limit: int) -> None:
        self._events: deque[Event] = deque(maxlen=limit)
        self._lock = Lock()

    def append(self, event_type: str, message: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(
                Event(
                    event_type=event_type,
                    message=message,
                    payload=payload,
                    timestamp=datetime.now(timezone.utc),
                )
            )

    def tail(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return [event.to_dict() for event in list(self._events)[-limit:]]
