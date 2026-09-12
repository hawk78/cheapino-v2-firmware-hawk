from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest

from cheapino_typing_lab.client import TelemetryClient
from cheapino_typing_lab.protocol import EventFlags, EventType, INVALID_POSITION


BRIDGE = os.environ.get("CHEAPINO_TELEMETRY_FIRMWARE_BRIDGE")


class FirmwareBridgeTransport:
    def __init__(self, executable: str) -> None:
        self.process = subprocess.Popen(
            [executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        rc = self.process.wait(timeout=2)
        if rc != 0:
            stderr = b"" if self.process.stderr is None else self.process.stderr.read()
            raise AssertionError(f"firmware bridge exited with {rc}: {stderr.decode(errors='replace')}")

    def __enter__(self) -> "FirmwareBridgeTransport":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def exchange(self, report: bytes) -> bytes:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(report)
        self.process.stdin.flush()
        response = self.process.stdout.read(32)
        if len(response) != 32:
            stderr = b"" if self.process.stderr is None else self.process.stderr.read()
            raise AssertionError(
                f"firmware bridge returned {len(response)} bytes; stderr={stderr.decode(errors='replace')}"
            )
        return response


@unittest.skipUnless(BRIDGE, "run via run-tests.sh to build the C firmware bridge")
class FirmwareBridgeTests(unittest.TestCase):
    def test_python_client_round_trips_through_real_firmware_protocol(self) -> None:
        assert BRIDGE is not None
        self.assertTrue(Path(BRIDGE).is_file())

        with FirmwareBridgeTransport(BRIDGE) as transport:
            client = TelemetryClient(transport)

            info = client.info()
            self.assertEqual(info.version, 1)
            self.assertEqual(info.event_size, 12)
            self.assertEqual(info.events_per_read, 2)
            self.assertEqual(info.report_size, 32)
            self.assertGreaterEqual(info.capacity, 2)

            self.assertFalse(client.status().capturing)
            self.assertTrue(client.start().capturing)

            marker_status = client.mark(0x4567, 7)
            self.assertEqual(marker_status.queued, 1)

            first = client.read()
            self.assertEqual(first.sequence, 0)
            self.assertEqual(len(first.events), 1)
            marker = first.events[0]
            self.assertEqual(marker.type, EventType.MARKER)
            self.assertEqual(marker.value, 0x4567)
            self.assertEqual(marker.aux, 7)
            self.assertEqual(marker.position, INVALID_POSITION)
            self.assertEqual(marker.flags, EventFlags.SYNTHETIC)

            second = client.read()
            self.assertEqual(second.sequence, 1)
            self.assertEqual(second.events, ())

            client.clear()
            after_clear = client.read()
            self.assertEqual(after_clear.sequence, 0)
            self.assertEqual(after_clear.events, ())

            self.assertFalse(client.stop().capturing)


if __name__ == "__main__":
    unittest.main()
