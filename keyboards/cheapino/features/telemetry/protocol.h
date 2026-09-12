#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define CHEAPINO_TELEMETRY_PROTOCOL_VERSION 1u
#define CHEAPINO_TELEMETRY_REPORT_SIZE 32u
#define CHEAPINO_TELEMETRY_EVENT_SIZE 12u
#define CHEAPINO_TELEMETRY_EVENTS_PER_READ 2u
#define CHEAPINO_TELEMETRY_INVALID_POSITION 0xFFu

enum cheapino_telemetry_command {
    CHEAPINO_TELEMETRY_GET_INFO = 0x80,
    CHEAPINO_TELEMETRY_STATUS   = 0x81,
    CHEAPINO_TELEMETRY_START    = 0x82,
    CHEAPINO_TELEMETRY_STOP     = 0x83,
    CHEAPINO_TELEMETRY_CLEAR    = 0x84,
    CHEAPINO_TELEMETRY_READ     = 0x85,
    CHEAPINO_TELEMETRY_MARK     = 0x86,
    CHEAPINO_TELEMETRY_PING     = 0x87,
};

enum cheapino_telemetry_event_type {
    CHEAPINO_TELEMETRY_EVENT_PHYSICAL    = 0x01,
    CHEAPINO_TELEMETRY_EVENT_RESOLVED    = 0x02,
    CHEAPINO_TELEMETRY_EVENT_POST_ACTION = 0x03,
    CHEAPINO_TELEMETRY_EVENT_MARKER      = 0x10,
};

enum cheapino_telemetry_event_flags {
    CHEAPINO_TELEMETRY_FLAG_PRESSED     = 1u << 0,
    CHEAPINO_TELEMETRY_FLAG_TAP         = 1u << 1,
    CHEAPINO_TELEMETRY_FLAG_INTERRUPTED = 1u << 2,
    CHEAPINO_TELEMETRY_FLAG_SYNTHETIC   = 1u << 3,
};

enum cheapino_telemetry_status_flags {
    CHEAPINO_TELEMETRY_STATUS_CAPTURING = 1u << 0,
    CHEAPINO_TELEMETRY_STATUS_DROPPED   = 1u << 1,
};

typedef struct __attribute__((packed)) {
    uint32_t timestamp_ms;
    uint16_t value;
    uint8_t  type;
    uint8_t  position;
    uint8_t  flags;
    uint8_t  layer;
    uint8_t  mods;
    uint8_t  aux;
} cheapino_telemetry_event_v1_t;

_Static_assert(sizeof(cheapino_telemetry_event_v1_t) == CHEAPINO_TELEMETRY_EVENT_SIZE, "telemetry event must stay wire-compatible");

static inline uint8_t cheapino_telemetry_pack_position(uint8_t row, uint8_t col) {
    return (uint8_t)(((row & 0x0Fu) << 4) | (col & 0x0Fu));
}

static inline uint16_t cheapino_telemetry_read_u16_le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static inline void cheapino_telemetry_write_u16_le(uint8_t *p, uint16_t value) {
    p[0] = (uint8_t)(value & 0xFFu);
    p[1] = (uint8_t)(value >> 8);
}

static inline void cheapino_telemetry_write_u32_le(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)(value & 0xFFu);
    p[1] = (uint8_t)((value >> 8) & 0xFFu);
    p[2] = (uint8_t)((value >> 16) & 0xFFu);
    p[3] = (uint8_t)((value >> 24) & 0xFFu);
}
