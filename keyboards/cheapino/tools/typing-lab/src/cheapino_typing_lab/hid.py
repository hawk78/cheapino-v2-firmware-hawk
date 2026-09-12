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
        for entry in hid.enumerate(vid or 0, pid or 0):
            if entry.get("usage_page") == RAW_HID_USAGE_PAGE and entry.get("usage") == RAW_HID_USAGE:
                candidates.append(entry)
        if not candidates:
            raise HidTransportError("Cheapino/VIA Raw HID interface not found")
        if len(candidates) > 1 and (vid is None or pid is None):
            rendered = ", ".join(
                f"{item.get('vendor_id', 0):04x}:{item.get('product_id', 0):04x}" for item in candidates
            )
            raise HidTransportError(f"multiple VIA Raw HID interfaces found ({rendered}); specify --vid and --pid")

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
        # hidapi's write() includes the report-id byte even for unnumbered reports.
        written = self.device.write(b"\x00" + report)
        if written not in (32, 33):
            raise HidTransportError(f"short Raw HID write: {written}")
        response = bytes(self.device.read(32, timeout_ms=1000))
        if len(response) != 32:
            raise HidTransportError(f"short Raw HID read: {len(response)}")
        return response
