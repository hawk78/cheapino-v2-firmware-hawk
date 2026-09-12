from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .client import TelemetryClient
from .hid import HidTransport
from .recorder import capture_jsonl


def _auto_int(value: str) -> int:
    return int(value, 0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cheapino-typing-lab")
    parser.add_argument("--vid", type=_auto_int, default=0xFEE3)
    parser.add_argument("--pid", type=_auto_int, default=0x0000)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info")
    sub.add_parser("status")
    sub.add_parser("doctor")

    capture = sub.add_parser("capture")
    capture.add_argument("--seconds", type=float, required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--poll-ms", type=float, default=5.0)

    mark = sub.add_parser("mark")
    mark.add_argument("marker_id", type=_auto_int)
    mark.add_argument("phase", type=_auto_int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    with HidTransport.open(vid=args.vid, pid=args.pid) as transport:
        client = TelemetryClient(transport)
        if args.command == "info":
            print(json.dumps(asdict(client.info()), indent=2))
        elif args.command == "status":
            status = client.status()
            print(
                json.dumps(
                    {
                        "capturing": status.capturing,
                        "flags": int(status.flags),
                        "queued": status.queued,
                        "dropped": status.dropped,
                        "timestamp_ms": status.timestamp_ms,
                    },
                    indent=2,
                )
            )
        elif args.command == "doctor":
            info = client.info()
            status = client.status()
            problems = []
            if info.event_size != 12 or info.events_per_read != 2 or info.report_size != 32:
                problems.append("unexpected wire geometry")
            if status.capturing:
                problems.append("capture is already armed")
            if status.dropped:
                problems.append(f"drop counter is non-zero ({status.dropped}); START or CLEAR resets it")
            print(
                json.dumps(
                    {
                        "ok": not problems,
                        "protocol": asdict(info),
                        "status": {
                            "capturing": status.capturing,
                            "queued": status.queued,
                            "dropped": status.dropped,
                            "timestamp_ms": status.timestamp_ms,
                        },
                        "problems": problems,
                    },
                    indent=2,
                )
            )
            return 0 if not problems else 2
        elif args.command == "capture":
            count = capture_jsonl(
                client,
                args.output,
                duration_s=args.seconds,
                poll_interval_s=args.poll_ms / 1000.0,
            )
            print(f"captured {count} events -> {args.output}")
        elif args.command == "mark":
            status = client.mark(args.marker_id, args.phase)
            print(json.dumps({"queued": status.queued, "dropped": status.dropped}))
    return 0
