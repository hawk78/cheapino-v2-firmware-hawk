from __future__ import annotations

import struct
import unittest

from cheapino_typing_lab.client import DroppedEventsError, TelemetryClient, TelemetryError
from cheapino_typing_lab.protocol import Command, Event, EventFlags, EventType, encode_event


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def exchange(self, report: bytes) -> bytes:
        self.requests.append(report)
        return self.responses.pop(0)


def read_response(sequence: int, events=(), dropped=0):
    report = bytearray(32)
    report[0] = Command.READ
    report[1] = 1
    struct.pack_into("<H", report, 2, sequence)
    report[4] = len(events)
    struct.pack_into("<H", report, 6, dropped)
    for index, event in enumerate(events):
        report[8 + 12 * index : 20 + 12 * index] = encode_event(event)
    return bytes(report)


class ClientTests(unittest.TestCase):
    def test_drain_until_empty(self):
        event = Event(1, 2, EventType.PHYSICAL, 0x12, EventFlags.PRESSED, 0, 0, 0)
        client = TelemetryClient(FakeTransport([read_response(0, [event]), read_response(1)]))
        self.assertEqual(list(client.drain()), [event])

    def test_sequence_gap_is_error(self):
        client = TelemetryClient(FakeTransport([read_response(4), read_response(6)]))
        client.read()
        with self.assertRaises(TelemetryError):
            client.read()

    def test_drop_is_error_by_default(self):
        client = TelemetryClient(FakeTransport([read_response(0, dropped=2)]))
        with self.assertRaises(DroppedEventsError):
            client.read()


if __name__ == "__main__":
    unittest.main()
