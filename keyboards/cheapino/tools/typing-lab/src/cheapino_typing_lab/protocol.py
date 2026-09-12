from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag
import struct

PROTOCOL_VERSION = 1
REPORT_SIZE = 32
EVENT_SIZE = 12
EVENTS_PER_READ = 2
INVALID_POSITION = 0xFF


class Command(IntEnum):
    GET_INFO = 0x80
    STATUS = 0x81
    START = 0x82
    STOP = 0x83
    CLEAR = 0x84
    READ = 0x85
    MARK = 0x86
    PING = 0x87


class EventType(IntEnum):
    PHYSICAL = 0x01
    RESOLVED = 0x02
    POST_ACTION = 0x03
    MARKER = 0x10


class EventFlags(IntFlag):
    PRESSED = 1 << 0
    TAP = 1 << 1
    INTERRUPTED = 1 << 2
    SYNTHETIC = 1 << 3


class StatusFlags(IntFlag):
    CAPTURING = 1 << 0
    DROPPED = 1 << 1


_EVENT = struct.Struct("<IHBBBBBB")
assert _EVENT.size == EVENT_SIZE


@dataclass(frozen=True, slots=True)
class Event:
    timestamp_ms: int
    value: int
    type: EventType
    position: int
    flags: EventFlags
    layer: int
    mods: int
    aux: int

    @property
    def row(self) -> int | None:
        return None if self.position == INVALID_POSITION else self.position >> 4

    @property
    def col(self) -> int | None:
        return None if self.position == INVALID_POSITION else self.position & 0x0F

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "timestamp_ms": self.timestamp_ms,
            "value": self.value,
            "type": self.type.name,
            "position": self.position,
            "row": self.row,
            "col": self.col,
            "flags": int(self.flags),
            "layer": self.layer,
            "mods": self.mods,
            "aux": self.aux,
        }


@dataclass(frozen=True, slots=True)
class Info:
    version: int
    event_size: int
    events_per_read: int
    capacity: int
    report_size: int


@dataclass(frozen=True, slots=True)
class Status:
    flags: StatusFlags
    queued: int
    dropped: int
    timestamp_ms: int

    @property
    def capturing(self) -> bool:
        return bool(self.flags & StatusFlags.CAPTURING)


@dataclass(frozen=True, slots=True)
class ReadResponse:
    sequence: int
    flags: StatusFlags
    dropped_low16: int
    events: tuple[Event, ...]


def empty_report(command: Command) -> bytearray:
    report = bytearray(REPORT_SIZE)
    report[0] = command
    return report


def marker_report(marker_id: int, phase: int) -> bytes:
    if not 0 <= marker_id <= 0xFFFF:
        raise ValueError("marker_id must fit in uint16")
    if not 0 <= phase <= 0xFF:
        raise ValueError("phase must fit in uint8")
    report = empty_report(Command.MARK)
    report[1] = phase
    struct.pack_into("<H", report, 2, marker_id)
    return bytes(report)


def decode_event(data: bytes | bytearray | memoryview) -> Event:
    if len(data) != EVENT_SIZE:
        raise ValueError(f"event must be {EVENT_SIZE} bytes")
    timestamp_ms, value, type_raw, position, flags, layer, mods, aux = _EVENT.unpack(data)
    return Event(
        timestamp_ms=timestamp_ms,
        value=value,
        type=EventType(type_raw),
        position=position,
        flags=EventFlags(flags),
        layer=layer,
        mods=mods,
        aux=aux,
    )


def encode_event(event: Event) -> bytes:
    return _EVENT.pack(
        event.timestamp_ms,
        event.value,
        int(event.type),
        event.position,
        int(event.flags),
        event.layer,
        event.mods,
        event.aux,
    )


def _validate_response(data: bytes, command: Command) -> None:
    if len(data) != REPORT_SIZE:
        raise ValueError(f"report must be {REPORT_SIZE} bytes")
    if data[0] != command:
        raise ValueError(f"unexpected response command 0x{data[0]:02x}; expected 0x{command:02x}")
    if data[1] != PROTOCOL_VERSION:
        raise ValueError(f"protocol version mismatch: firmware={data[1]} host={PROTOCOL_VERSION}")


def decode_info(data: bytes) -> Info:
    _validate_response(data, Command.GET_INFO)
    return Info(
        version=data[1],
        event_size=data[2],
        events_per_read=data[3],
        capacity=struct.unpack_from("<H", data, 4)[0],
        report_size=data[6],
    )


def decode_status(data: bytes, command: Command = Command.STATUS) -> Status:
    _validate_response(data, command)
    return Status(
        flags=StatusFlags(data[2]),
        queued=struct.unpack_from("<H", data, 4)[0],
        dropped=struct.unpack_from("<I", data, 6)[0],
        timestamp_ms=struct.unpack_from("<I", data, 10)[0],
    )


def decode_read(data: bytes) -> ReadResponse:
    _validate_response(data, Command.READ)
    count = data[4]
    if count > EVENTS_PER_READ:
        raise ValueError(f"firmware returned impossible event count: {count}")
    events = tuple(
        decode_event(data[8 + i * EVENT_SIZE : 8 + (i + 1) * EVENT_SIZE])
        for i in range(count)
    )
    return ReadResponse(
        sequence=struct.unpack_from("<H", data, 2)[0],
        flags=StatusFlags(data[5]),
        dropped_low16=struct.unpack_from("<H", data, 6)[0],
        events=events,
    )
