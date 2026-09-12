from __future__ import annotations

import json
from pathlib import Path
import time

from .client import TelemetryClient


def capture_jsonl(
    client: TelemetryClient,
    output: Path,
    *,
    duration_s: float,
    poll_interval_s: float = 0.005,
) -> int:
    if duration_s <= 0:
        raise ValueError("duration_s must be > 0")
    if poll_interval_s < 0:
        raise ValueError("poll_interval_s must be >= 0")

    info = client.info()
    client.clear()
    client.start()
    deadline = time.monotonic() + duration_s
    written = 0

    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "meta", "protocol": info.version, "event_size": info.event_size}) + "\n")
        try:
            while time.monotonic() < deadline:
                response = client.read()
                for event in response.events:
                    stream.write(json.dumps({"kind": "event", **event.to_dict()}, separators=(",", ":")) + "\n")
                    written += 1
                if not response.events and poll_interval_s:
                    time.sleep(poll_interval_s)
        finally:
            client.stop()

        for event in client.drain():
            stream.write(json.dumps({"kind": "event", **event.to_dict()}, separators=(",", ":")) + "\n")
            written += 1
        status = client.status()
        stream.write(
            json.dumps(
                {
                    "kind": "end",
                    "events": written,
                    "dropped": status.dropped,
                    "firmware_timestamp_ms": status.timestamp_ms,
                },
                separators=(",", ":"),
            )
            + "\n"
        )

    return written
