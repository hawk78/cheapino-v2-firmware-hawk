from __future__ import annotations

import struct
import unittest

from cheapino_typing_lab.protocol import (
    Command,
    Event,
    EventFlags,
    EventType,
    StatusFlags,
    decode_event,
    decode_info,
    decode_read,
    decode_status,
    encode_event,
    marker_report,
)


class ProtocolTests(unittest.TestCase):
    def test_event_round_trip(self):
        original = Event(0x12345678, 0xABCD, EventType.RESOLVED, 0x2B, EventFlags.PRESSED | EventFlags.TAP, 4, 0x11, 3)
        decoded = decode_event(encode_event(original))
        self.assertEqual(decoded, original)
        self.assertEqual(decoded.row, 2)
        self.assertEqual(decoded.col, 11)

    def test_info(self):
        report = bytearray(32)
        report[0] = Command.GET_INFO
        report[1] = 1
        report[2] = 12
        report[3] = 2
        struct.pack_into("<H", report, 4, 1024)
        report[6] = 32
        info = decode_info(bytes(report))
        self.assertEqual((info.event_size, info.events_per_read, info.capacity, info.report_size), (12, 2, 1024, 32))

    def test_status(self):
        report = bytearray(32)
        report[0] = Command.STATUS
        report[1] = 1
        report[2] = int(StatusFlags.CAPTURING | StatusFlags.DROPPED)
        struct.pack_into("<HII", report, 4, 7, 9, 1234)
        status = decode_status(bytes(report))
        self.assertTrue(status.capturing)
        self.assertEqual(status.queued, 7)
        self.assertEqual(status.dropped, 9)
        self.assertEqual(status.timestamp_ms, 1234)

    def test_two_event_read(self):
        first = Event(1, 2, EventType.PHYSICAL, 0x12, EventFlags.PRESSED, 0, 0, 0)
        second = Event(3, 4, EventType.POST_ACTION, 0x34, EventFlags(0), 2, 8, 0)
        report = bytearray(32)
        report[0] = Command.READ
        report[1] = 1
        struct.pack_into("<H", report, 2, 42)
        report[4] = 2
        report[5] = int(StatusFlags.CAPTURING)
        report[8:20] = encode_event(first)
        report[20:32] = encode_event(second)
        decoded = decode_read(bytes(report))
        self.assertEqual(decoded.sequence, 42)
        self.assertEqual(decoded.events, (first, second))

    def test_marker_request(self):
        report = marker_report(0x1234, 7)
        self.assertEqual(len(report), 32)
        self.assertEqual(report[:4], bytes([Command.MARK, 7, 0x34, 0x12]))


if __name__ == "__main__":
    unittest.main()
