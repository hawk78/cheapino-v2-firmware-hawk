#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#define CHEAPINO_TELEMETRY_RING_CAPACITY 4
#include "ring.h"

static cheapino_telemetry_event_v1_t event(uint16_t value) {
    cheapino_telemetry_event_v1_t e = {0};
    e.value = value;
    return e;
}

int main(void) {
    cheapino_telemetry_event_v1_t layout = {
        .timestamp_ms = 0x44332211u,
        .value = 0x6655u,
        .type = 0x77u,
        .position = 0x88u,
        .flags = 0x99u,
        .layer = 0xAAu,
        .mods = 0xBBu,
        .aux = 0xCCu,
    };
    const uint8_t *wire = (const uint8_t *)&layout;
    const uint8_t expected[CHEAPINO_TELEMETRY_EVENT_SIZE] = {
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC
    };
    for (size_t i = 0; i < sizeof(expected); ++i) {
        assert(wire[i] == expected[i]);
    }

    cheapino_telemetry_ring_t ring;
    cheapino_telemetry_ring_init(&ring);
    assert(cheapino_telemetry_ring_count(&ring) == 0);

    for (uint16_t i = 1; i <= 4; ++i) {
        cheapino_telemetry_event_v1_t e = event(i);
        assert(cheapino_telemetry_ring_push(&ring, &e));
    }
    cheapino_telemetry_event_v1_t overflow = event(99);
    assert(!cheapino_telemetry_ring_push(&ring, &overflow));
    assert(cheapino_telemetry_ring_dropped(&ring) == 1);

    for (uint16_t i = 1; i <= 2; ++i) {
        cheapino_telemetry_event_v1_t out;
        assert(cheapino_telemetry_ring_pop(&ring, &out));
        assert(out.value == i);
    }
    for (uint16_t i = 5; i <= 6; ++i) {
        cheapino_telemetry_event_v1_t e = event(i);
        assert(cheapino_telemetry_ring_push(&ring, &e));
    }
    for (uint16_t i = 3; i <= 6; ++i) {
        cheapino_telemetry_event_v1_t out;
        assert(cheapino_telemetry_ring_pop(&ring, &out));
        assert(out.value == i);
    }
    assert(cheapino_telemetry_ring_count(&ring) == 0);

    cheapino_telemetry_ring_clear(&ring);
    assert(cheapino_telemetry_ring_dropped(&ring) == 0);
    puts("ring tests: ok");
    return 0;
}
