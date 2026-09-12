#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "protocol.h"

#ifndef CHEAPINO_TELEMETRY_RING_CAPACITY
#    define CHEAPINO_TELEMETRY_RING_CAPACITY 1024u
#endif

#if CHEAPINO_TELEMETRY_RING_CAPACITY < 2
#    error "CHEAPINO_TELEMETRY_RING_CAPACITY must be >= 2"
#endif

#if CHEAPINO_TELEMETRY_RING_CAPACITY > UINT16_MAX
#    error "CHEAPINO_TELEMETRY_RING_CAPACITY must fit in uint16_t"
#endif

typedef struct {
    cheapino_telemetry_event_v1_t events[CHEAPINO_TELEMETRY_RING_CAPACITY];
    uint16_t                      head;
    uint16_t                      tail;
    uint16_t                      count;
    uint32_t                      dropped;
} cheapino_telemetry_ring_t;

void     cheapino_telemetry_ring_init(cheapino_telemetry_ring_t *ring);
void     cheapino_telemetry_ring_clear(cheapino_telemetry_ring_t *ring);
bool     cheapino_telemetry_ring_push(cheapino_telemetry_ring_t *ring, const cheapino_telemetry_event_v1_t *event);
bool     cheapino_telemetry_ring_pop(cheapino_telemetry_ring_t *ring, cheapino_telemetry_event_v1_t *event);
uint16_t cheapino_telemetry_ring_count(const cheapino_telemetry_ring_t *ring);
uint32_t cheapino_telemetry_ring_dropped(const cheapino_telemetry_ring_t *ring);
