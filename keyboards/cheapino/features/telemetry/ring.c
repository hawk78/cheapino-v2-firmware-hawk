#include "ring.h"

#include <string.h>

void cheapino_telemetry_ring_init(cheapino_telemetry_ring_t *ring) {
    memset(ring, 0, sizeof(*ring));
}

void cheapino_telemetry_ring_clear(cheapino_telemetry_ring_t *ring) {
    ring->head    = 0;
    ring->tail    = 0;
    ring->count   = 0;
    ring->dropped = 0;
}

bool cheapino_telemetry_ring_push(cheapino_telemetry_ring_t *ring, const cheapino_telemetry_event_v1_t *event) {
    if (ring->count == CHEAPINO_TELEMETRY_RING_CAPACITY) {
        ring->dropped++;
        return false;
    }

    ring->events[ring->head] = *event;
    ring->head++;
    if (ring->head == CHEAPINO_TELEMETRY_RING_CAPACITY) {
        ring->head = 0;
    }
    ring->count++;
    return true;
}

bool cheapino_telemetry_ring_pop(cheapino_telemetry_ring_t *ring, cheapino_telemetry_event_v1_t *event) {
    if (ring->count == 0) {
        return false;
    }

    *event = ring->events[ring->tail];
    ring->tail++;
    if (ring->tail == CHEAPINO_TELEMETRY_RING_CAPACITY) {
        ring->tail = 0;
    }
    ring->count--;
    return true;
}

uint16_t cheapino_telemetry_ring_count(const cheapino_telemetry_ring_t *ring) {
    return ring->count;
}

uint32_t cheapino_telemetry_ring_dropped(const cheapino_telemetry_ring_t *ring) {
    return ring->dropped;
}
