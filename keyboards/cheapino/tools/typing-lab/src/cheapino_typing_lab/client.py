from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .protocol import (
    Command,
    Info,
    ReadResponse,
    Status,
    decode_info,
    decode_read,
    decode_status,
    empty_report,
    marker_report,
)


class Transport(Protocol):
    def exchange(self, report: bytes) -> bytes: ...


class TelemetryError(RuntimeError):
    pass


class DroppedEventsError(TelemetryError):
    pass


@dataclass
class TelemetryClient:
    transport: Transport
    _expected_read_sequence: int | None = None

    def _exchange(self, report: bytes | bytearray) -> bytes:
        if len(report) != 32:
            raise ValueError("telemetry reports are exactly 32 bytes")
        response = self.transport.exchange(bytes(report))
        if len(response) != 32:
            raise TelemetryError(f"transport returned {len(response)} bytes, expected 32")
        return response

    def info(self) -> Info:
        return decode_info(self._exchange(empty_report(Command.GET_INFO)))

    def status(self) -> Status:
        return decode_status(self._exchange(empty_report(Command.STATUS)))

    def start(self) -> Status:
        self._expected_read_sequence = None
        return decode_status(self._exchange(empty_report(Command.START)), Command.START)

    def stop(self) -> Status:
        return decode_status(self._exchange(empty_report(Command.STOP)), Command.STOP)

    def clear(self) -> Status:
        self._expected_read_sequence = None
        return decode_status(self._exchange(empty_report(Command.CLEAR)), Command.CLEAR)

    def mark(self, marker_id: int, phase: int) -> Status:
        return decode_status(self._exchange(marker_report(marker_id, phase)), Command.MARK)

    def read(self, *, reject_drops: bool = True) -> ReadResponse:
        response = decode_read(self._exchange(empty_report(Command.READ)))
        if self._expected_read_sequence is not None and response.sequence != self._expected_read_sequence:
            raise TelemetryError(
                f"READ response sequence discontinuity: got {response.sequence}, "
                f"expected {self._expected_read_sequence}"
            )
        self._expected_read_sequence = (response.sequence + 1) & 0xFFFF
        if reject_drops and response.dropped_low16:
            raise DroppedEventsError(f"firmware reports at least {response.dropped_low16} dropped event(s)")
        return response

    def drain(self, *, reject_drops: bool = True, max_reads: int = 65536):
        for _ in range(max_reads):
            response = self.read(reject_drops=reject_drops)
            yield from response.events
            if not response.events:
                return
        raise TelemetryError("drain exceeded max_reads; producer may be outrunning host")
