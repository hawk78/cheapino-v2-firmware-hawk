from __future__ import annotations

import unittest
from unittest.mock import patch

from cheapino_typing_lab.hid import HidTransport, HidTransportError, RAW_HID_USAGE, RAW_HID_USAGE_PAGE


class FakeDevice:
    def __init__(self, response=None):
        self.opened_path = None
        self.writes = []
        self.reads = []
        self.closed = False
        self.response = list(range(32)) if response is None else response

    def open_path(self, path):
        self.opened_path = path

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def read(self, length, timeout_ms=0):
        self.reads.append((length, timeout_ms))
        return self.response

    def close(self):
        self.closed = True


class FakeHidModule:
    def __init__(self, entries):
        self.entries = entries
        self.dev = FakeDevice()
        self.enumerate_args = None

    def enumerate(self, vid, pid):
        self.enumerate_args = (vid, pid)
        return self.entries

    def device(self):
        return self.dev


def entry(pid, path):
    return {
        "vendor_id": 0xFEE3,
        "product_id": pid,
        "usage_page": RAW_HID_USAGE_PAGE,
        "usage": RAW_HID_USAGE,
        "path": path,
    }


class HidTransportTests(unittest.TestCase):
    def test_pid_zero_is_matched_exactly_not_as_wildcard(self):
        fake = FakeHidModule([entry(0x1234, b"other"), entry(0x0000, b"cheapino")])
        with patch("cheapino_typing_lab.hid._load_hid", return_value=fake):
            transport = HidTransport.open(vid=0xFEE3, pid=0x0000)
        self.assertEqual(fake.enumerate_args, (0xFEE3, 0))
        self.assertEqual(transport.device.opened_path, b"cheapino")

    def test_multiple_matching_devices_are_rejected(self):
        fake = FakeHidModule([entry(0x0000, b"one"), entry(0x0000, b"two")])
        with patch("cheapino_typing_lab.hid._load_hid", return_value=fake):
            with self.assertRaises(HidTransportError):
                HidTransport.open(vid=0xFEE3, pid=0x0000)

    def test_exchange_uses_zero_report_id_and_timeout(self):
        device = FakeDevice(response=[7] * 32)
        transport = HidTransport(device)
        payload = bytes(range(32))
        response = transport.exchange(payload)
        self.assertEqual(device.writes, [b"\x00" + payload])
        self.assertEqual(device.reads, [(32, 1000)])
        self.assertEqual(response, bytes([7] * 32))


if __name__ == "__main__":
    unittest.main()
