from datetime import datetime
from typing import Any


def trace_step(component: str, message: str, payload: Any | None = None) -> None:
    """Print a compact trace line used while debugging the API execution flow."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[TRACE][{timestamp}][{component}] {message}")
    if payload is not None:
        print(f"[TRACE][{component}][payload] {payload}")
