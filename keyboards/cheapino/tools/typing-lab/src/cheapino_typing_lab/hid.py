from __future__ import annotations

from dataclasses import dataclass

RAW_HID_USAGE_PAGE = 0xFF60
RAW_HID_USAGE = 0x61


class HidTransportError(RuntimeError):
    pass


def _load_hid():
    try:
        import hid  # type: ignore
    except ImportError as exc:
        raise HidTransportError(
            "hidapi is required for real hardware access; install the 'hid' optional dependency"
        ) from exc
    return hid


@dataclass
class HidTransport:
    device: object

    @classmethod
    def open(cls, *, vid: int | None = None, pid: int | None = None) -> "HidTransport":
        hid = _load_hid()
        candidates = []
        # HIDAPI treats zero VID/PID arguments as wildcards. Cheapino's PID is
        # actually 0x0000, so enforce VID/PID equality ourselves after enumeration.
        for entry in hid.enumerate(vid or 0, 0):
            if vid is not None and entry.get("vendor_id") != vid:
                continue
            if pid is not None and entry.get("product_id") != pid:
                continue
            if entry.get("usage_page") != RAW_HID_USAGE_PAGE or entry.get("usage") != RAW_HID_USAGE:
                continue
            candidates.append(entry)

        if not candidates:
            raise HidTransportError("Cheapino/VIA Raw HID interface not found")
        if len(candidates) != 1:
            rendered = ", ".join(
                f"{item.get('vendor_id', 0):04x}:{item.get('product_id', 0):04x}" for item in candidates
            )
            raise HidTransportError(f"multiple matching VIA Raw HID interfaces found ({rendered})")

        dev = hid.device()
        dev.open_path(candidates[0]["path"])
        return cls(dev)

    def close(self) -> None:
        self.device.close()

    def __enter__(self) -> "HidTransport":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def exchange(self, report: bytes) -> bytes:
        if len(report) != 32:
            raise ValueError("Raw HID payload must be exactly 32 bytes")
        # HIDAPI requires an explicit zero report-id byte for unnumbered reports.
        written = self.device.write(b"\x00" + report)
        if written != 33:
            raise HidTransportError(f"short Raw HID write: {written}")
        response = bytes(self.device.read(32, 1000))
        if len(response) != 32:
            raise HidTransportError(f"short Raw HID read: {len(response)}")
        return response
