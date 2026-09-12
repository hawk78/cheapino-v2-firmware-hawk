from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cheapino_typing_lab.protocol import Event, EventFlags, EventType
from cheapino_typing_lab.recorder import capture_jsonl


class FakeClient:
    def __init__(self, *, read_response=None, read_error=None, drain_events=()):
        self.read_response = read_response
        self.read_error = read_error
        self.drain_events = tuple(drain_events)
        self.start_calls = 0
        self.stop_calls = 0
        self.status_calls = 0

    def info(self):
        return SimpleNamespace(version=1, event_size=12)

    def start(self):
        self.start_calls += 1
        return SimpleNamespace(capturing=True)

    def stop(self):
        self.stop_calls += 1
        return SimpleNamespace(capturing=False)

    def read(self):
        if self.read_error is not None:
            raise self.read_error
        return self.read_response or SimpleNamespace(events=())

    def drain(self):
        return iter(self.drain_events)

    def status(self):
        self.status_calls += 1
        return SimpleNamespace(dropped=0, timestamp_ms=1234)


class RecorderTests(unittest.TestCase):
    def test_existing_output_never_arms_keyboard(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "capture.jsonl"
            output.write_text("already here\n", encoding="utf-8")
            client = FakeClient()

            with self.assertRaises(FileExistsError):
                capture_jsonl(client, output, duration_s=1)

            self.assertEqual(client.start_calls, 0)
            self.assertEqual(client.stop_calls, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "already here\n")

    def test_read_failure_still_stops_capture(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "capture.jsonl"
            client = FakeClient(read_error=RuntimeError("boom"))

            with patch("cheapino_typing_lab.recorder.time.monotonic", side_effect=[0.0, 0.0]):
                with self.assertRaisesRegex(RuntimeError, "boom"):
                    capture_jsonl(client, output, duration_s=1, poll_interval_s=0)

            self.assertEqual(client.start_calls, 1)
            self.assertEqual(client.stop_calls, 1)

    def test_capture_writes_events_and_clean_end_record(self):
        first = Event(10, 0, EventType.PHYSICAL, 0x12, EventFlags.PRESSED, 0, 0, 0)
        trailing = Event(11, 0x4567, EventType.MARKER, 0xFF, EventFlags.SYNTHETIC, 0, 0, 7)
        client = FakeClient(
            read_response=SimpleNamespace(events=(first,)),
            drain_events=(trailing,),
        )

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "capture.jsonl"
            with patch("cheapino_typing_lab.recorder.time.monotonic", side_effect=[0.0, 0.0, 2.0]):
                count = capture_jsonl(client, output, duration_s=1, poll_interval_s=0)

            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(count, 2)
        self.assertEqual(client.start_calls, 1)
        self.assertEqual(client.stop_calls, 1)
        self.assertEqual(records[0]["kind"], "meta")
        self.assertEqual([record["kind"] for record in records[1:3]], ["event", "event"])
        self.assertEqual(records[-1], {"kind": "end", "events": 2, "dropped": 0, "firmware_timestamp_ms": 1234})


if __name__ == "__main__":
    unittest.main()
