from __future__ import annotations

import struct
import unittest

from cheapino_typing_lab.protocol import (
    Command,
    Event,
    EventFlags,
    EventType,
    PROTOCOL_VERSION,
    StatusFlags,
    decode_event,
    decode_info,
    decode_read,
    decode_status,
    empty_report,
    encode_event,
    marker_report,
)


class ProtocolTests(unittest.TestCase):
    def test_event_round_trip_and_wire_layout(self):
        original = Event(
            0x44332211,
            0x6655,
            EventType.RESOLVED,
            0x88,
            EventFlags.PRESSED | EventFlags.SYNTHETIC,
            0xAA,
            0xBB,
            0xCC,
        )
        encoded = encode_event(original)
        self.assertEqual(
            encoded,
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x02, 0x88, 0x09, 0xAA, 0xBB, 0xCC]),
        )
        self.assertEqual(decode_event(encoded), original)

    def test_position_decode(self):
        event = Event(1, 2, EventType.RESOLVED, 0x2B, EventFlags.PRESSED, 4, 0x11, 3)
        self.assertEqual(event.row, 2)
        self.assertEqual(event.col, 11)

    def test_request_contains_protocol_version(self):
        report = empty_report(Command.STATUS)
        self.assertEqual(report[:2], bytes([Command.STATUS, PROTOCOL_VERSION]))

    def test_info(self):
        report = bytearray(32)
        report[0] = Command.GET_INFO
        report[1] = PROTOCOL_VERSION
        report[2] = 12
        report[3] = 2
        struct.pack_into("<H", report, 4, 1024)
        report[6] = 32
        info = decode_info(bytes(report))
        self.assertEqual((info.event_size, info.events_per_read, info.capacity, info.report_size), (12, 2, 1024, 32))

    def test_response_version_mismatch_is_rejected(self):
        report = bytearray(32)
        report[0] = Command.GET_INFO
        report[1] = PROTOCOL_VERSION + 1
        with self.assertRaises(ValueError):
            decode_info(bytes(report))

    def test_status(self):
        report = bytearray(32)
        report[0] = Command.STATUS
        report[1] = PROTOCOL_VERSION
        report[2] = int(StatusFlags.CAPTURING | StatusFlags.DROPPED)
        struct.pack_into("<HII", report, 4, 7, 9, 1234)
        status = decode_status(bytes(report))
        self.assertTrue(status.capturing)
        self.assertEqual(status.queued, 7)
        self.assertEqual(status.dropped, 9)
        self.assertEqual(status.timestamp_ms, 1234)

    def test_zero_one_two_event_read(self):
        first = Event(1, 2, EventType.PHYSICAL, 0x12, EventFlags.PRESSED, 0, 0, 0)
        second = Event(3, 4, EventType.POST_ACTION, 0x34, EventFlags(0), 2, 8, 0)
        for events in ((), (first,), (first, second)):
            report = bytearray(32)
            report[0] = Command.READ
            report[1] = PROTOCOL_VERSION
            struct.pack_into("<H", report, 2, 42)
            report[4] = len(events)
            report[5] = int(StatusFlags.CAPTURING)
            for index, event in enumerate(events):
                report[8 + index * 12 : 20 + index * 12] = encode_event(event)
            decoded = decode_read(bytes(report))
            self.assertEqual(decoded.sequence, 42)
            self.assertEqual(decoded.events, events)

    def test_marker_request(self):
        report = marker_report(0x1234, 7)
        self.assertEqual(len(report), 32)
        self.assertEqual(report[:5], bytes([Command.MARK, PROTOCOL_VERSION, 7, 0x34, 0x12]))


if __name__ == "__main__":
    unittest.main()
