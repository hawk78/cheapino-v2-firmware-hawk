#include "telemetry.h"

#include <string.h>

#include "atomic_util.h"
#include "matrix.h"
#include "protocol.h"
#include "ring.h"
#include "timer.h"
#include "via.h"

static cheapino_telemetry_ring_t telemetry_ring;
static matrix_row_t              previous_matrix[MATRIX_ROWS];
static bool                      previous_matrix_valid;
static bool                      capture_enabled;
static uint16_t                  response_sequence;
static bool                      initialized;

static void telemetry_init_once(void) {
    if (initialized) {
        return;
    }
    cheapino_telemetry_ring_init(&telemetry_ring);
    initialized = true;
}

static uint8_t telemetry_layer(void) {
    return get_highest_layer(layer_state | default_layer_state);
}

static uint8_t telemetry_mods(void) {
    return get_mods();
}

static uint8_t telemetry_position(const keyrecord_t *record) {
    const uint8_t row = record->event.key.row;
    const uint8_t col = record->event.key.col;
    if (row >= 16u || col >= 16u) {
        return CHEAPINO_TELEMETRY_INVALID_POSITION;
    }
    return cheapino_telemetry_pack_position(row, col);
}

static void telemetry_push(const cheapino_telemetry_event_v1_t *event) {
    ATOMIC_BLOCK_RESTORESTATE {
        cheapino_telemetry_ring_push(&telemetry_ring, event);
    }
}

static void telemetry_snapshot_matrix(void) {
    for (uint8_t row = 0; row < MATRIX_ROWS; ++row) {
        previous_matrix[row] = matrix_get_row(row);
    }
    previous_matrix_valid = true;
}

static uint8_t telemetry_status_flags(void) {
    uint8_t flags = 0;
    if (capture_enabled) {
        flags |= CHEAPINO_TELEMETRY_STATUS_CAPTURING;
    }
    ATOMIC_BLOCK_RESTORESTATE {
        if (cheapino_telemetry_ring_dropped(&telemetry_ring) != 0) {
            flags |= CHEAPINO_TELEMETRY_STATUS_DROPPED;
        }
    }
    return flags;
}

static void telemetry_clear(void);

static void telemetry_write_status(uint8_t *data, uint8_t command) {
    uint16_t queued;
    uint32_t dropped;
    ATOMIC_BLOCK_RESTORESTATE {
        queued  = cheapino_telemetry_ring_count(&telemetry_ring);
        dropped = cheapino_telemetry_ring_dropped(&telemetry_ring);
    }

    memset(data, 0, CHEAPINO_TELEMETRY_REPORT_SIZE);
    data[0] = command;
    data[1] = CHEAPINO_TELEMETRY_PROTOCOL_VERSION;
    data[2] = telemetry_status_flags();
    cheapino_telemetry_write_u16_le(&data[4], queued);
    cheapino_telemetry_write_u32_le(&data[6], dropped);
    cheapino_telemetry_write_u32_le(&data[10], timer_read32());
}

static void telemetry_start(void) {
    telemetry_init_once();
    telemetry_clear();
    telemetry_snapshot_matrix();
    capture_enabled = true;
}

static void telemetry_stop(void) {
    capture_enabled = false;
}

static void telemetry_clear(void) {
    telemetry_init_once();
    ATOMIC_BLOCK_RESTORESTATE {
        cheapino_telemetry_ring_clear(&telemetry_ring);
    }
    response_sequence = 0;
}

static void telemetry_mark(uint16_t marker_id, uint8_t phase) {
    if (!capture_enabled) {
        return;
    }

    const cheapino_telemetry_event_v1_t event = {
        .timestamp_ms = timer_read32(),
        .value        = marker_id,
        .type         = CHEAPINO_TELEMETRY_EVENT_MARKER,
        .position     = CHEAPINO_TELEMETRY_INVALID_POSITION,
        .flags        = CHEAPINO_TELEMETRY_FLAG_SYNTHETIC,
        .layer        = telemetry_layer(),
        .mods         = telemetry_mods(),
        .aux          = phase,
    };
    telemetry_push(&event);
}

void cheapino_telemetry_scan_matrix(void) {
    telemetry_init_once();
    if (!capture_enabled) {
        return;
    }
    if (!previous_matrix_valid) {
        telemetry_snapshot_matrix();
        return;
    }

    for (uint8_t row = 0; row < MATRIX_ROWS; ++row) {
        const matrix_row_t now     = matrix_get_row(row);
        matrix_row_t       changed = now ^ previous_matrix[row];
        while (changed != 0) {
            const uint8_t      col = (uint8_t)__builtin_ctz((unsigned int)changed);
            const matrix_row_t bit = ((matrix_row_t)1u << col);
            const cheapino_telemetry_event_v1_t event = {
                .timestamp_ms = timer_read32(),
                .value        = 0,
                .type         = CHEAPINO_TELEMETRY_EVENT_PHYSICAL,
                .position     = cheapino_telemetry_pack_position(row, col),
                .flags        = (now & bit) ? CHEAPINO_TELEMETRY_FLAG_PRESSED : 0,
                .layer        = telemetry_layer(),
                .mods         = telemetry_mods(),
                .aux          = 0,
            };
            telemetry_push(&event);
            changed &= ~bit;
        }
        previous_matrix[row] = now;
    }
}

void cheapino_telemetry_record_resolved(uint16_t keycode, keyrecord_t *record) {
    telemetry_init_once();
    if (!capture_enabled) {
        return;
    }

    uint8_t flags = record->event.pressed ? CHEAPINO_TELEMETRY_FLAG_PRESSED : 0;
    if (record->tap.count != 0) {
        flags |= CHEAPINO_TELEMETRY_FLAG_TAP;
    }
    if (record->tap.interrupted) {
        flags |= CHEAPINO_TELEMETRY_FLAG_INTERRUPTED;
    }

    const cheapino_telemetry_event_v1_t event = {
        .timestamp_ms = timer_read32(),
        .value        = keycode,
        .type         = CHEAPINO_TELEMETRY_EVENT_RESOLVED,
        .position     = telemetry_position(record),
        .flags        = flags,
        .layer        = telemetry_layer(),
        .mods         = telemetry_mods(),
        .aux          = record->tap.count,
    };
    telemetry_push(&event);
}

void cheapino_telemetry_record_post_action(uint16_t keycode, keyrecord_t *record) {
    telemetry_init_once();
    if (!capture_enabled) {
        return;
    }

    const cheapino_telemetry_event_v1_t event = {
        .timestamp_ms = timer_read32(),
        .value        = keycode,
        .type         = CHEAPINO_TELEMETRY_EVENT_POST_ACTION,
        .position     = telemetry_position(record),
        .flags        = record->event.pressed ? CHEAPINO_TELEMETRY_FLAG_PRESSED : 0,
        .layer        = telemetry_layer(),
        .mods         = telemetry_mods(),
        .aux          = 0,
    };
    telemetry_push(&event);
}

static void telemetry_read_events(uint8_t *data) {
    cheapino_telemetry_event_v1_t events[CHEAPINO_TELEMETRY_EVENTS_PER_READ];
    uint8_t                       event_count = 0;
    uint32_t                      dropped;

    ATOMIC_BLOCK_RESTORESTATE {
        while (event_count < CHEAPINO_TELEMETRY_EVENTS_PER_READ && cheapino_telemetry_ring_pop(&telemetry_ring, &events[event_count])) {
            event_count++;
        }
        dropped = cheapino_telemetry_ring_dropped(&telemetry_ring);
    }

    memset(data, 0, CHEAPINO_TELEMETRY_REPORT_SIZE);
    data[0] = CHEAPINO_TELEMETRY_READ;
    data[1] = CHEAPINO_TELEMETRY_PROTOCOL_VERSION;
    cheapino_telemetry_write_u16_le(&data[2], response_sequence++);
    data[4] = event_count;
    data[5] = telemetry_status_flags();
    cheapino_telemetry_write_u16_le(&data[6], (uint16_t)dropped);
    for (uint8_t i = 0; i < event_count; ++i) {
        memcpy(&data[8 + i * CHEAPINO_TELEMETRY_EVENT_SIZE], &events[i], CHEAPINO_TELEMETRY_EVENT_SIZE);
    }
}

bool cheapino_telemetry_raw_hid_receive(uint8_t *data, uint8_t length) {
    telemetry_init_once();
    if (length != CHEAPINO_TELEMETRY_REPORT_SIZE) {
        return false;
    }

    const uint8_t command = data[0];
    if (command < CHEAPINO_TELEMETRY_GET_INFO || command > CHEAPINO_TELEMETRY_PING) {
        return false;
    }
    if (data[1] != CHEAPINO_TELEMETRY_PROTOCOL_VERSION) {
        return false;
    }

    switch (command) {
        case CHEAPINO_TELEMETRY_GET_INFO:
            memset(data, 0, CHEAPINO_TELEMETRY_REPORT_SIZE);
            data[0] = CHEAPINO_TELEMETRY_GET_INFO;
            data[1] = CHEAPINO_TELEMETRY_PROTOCOL_VERSION;
            data[2] = CHEAPINO_TELEMETRY_EVENT_SIZE;
            data[3] = CHEAPINO_TELEMETRY_EVENTS_PER_READ;
            cheapino_telemetry_write_u16_le(&data[4], CHEAPINO_TELEMETRY_RING_CAPACITY);
            data[6] = CHEAPINO_TELEMETRY_REPORT_SIZE;
            return true;
        case CHEAPINO_TELEMETRY_STATUS:
            telemetry_write_status(data, CHEAPINO_TELEMETRY_STATUS);
            return true;
        case CHEAPINO_TELEMETRY_START:
            telemetry_start();
            telemetry_write_status(data, CHEAPINO_TELEMETRY_START);
            return true;
        case CHEAPINO_TELEMETRY_STOP:
            telemetry_stop();
            telemetry_write_status(data, CHEAPINO_TELEMETRY_STOP);
            return true;
        case CHEAPINO_TELEMETRY_CLEAR:
            telemetry_clear();
            telemetry_write_status(data, CHEAPINO_TELEMETRY_CLEAR);
            return true;
        case CHEAPINO_TELEMETRY_READ:
            telemetry_read_events(data);
            return true;
        case CHEAPINO_TELEMETRY_MARK: {
            const uint8_t  phase     = data[2];
            const uint16_t marker_id = cheapino_telemetry_read_u16_le(&data[3]);
            telemetry_mark(marker_id, phase);
            telemetry_write_status(data, CHEAPINO_TELEMETRY_MARK);
            return true;
        }
        case CHEAPINO_TELEMETRY_PING:
            memset(data, 0, CHEAPINO_TELEMETRY_REPORT_SIZE);
            data[0] = CHEAPINO_TELEMETRY_PING;
            data[1] = CHEAPINO_TELEMETRY_PROTOCOL_VERSION;
            cheapino_telemetry_write_u32_le(&data[2], timer_read32());
            return true;
        default:
            return false;
    }
}

void matrix_scan_kb(void) {
    cheapino_telemetry_scan_matrix();
    matrix_scan_user();
}

bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    cheapino_telemetry_record_resolved(keycode, record);
    return process_record_user(keycode, record);
}

void post_process_record_kb(uint16_t keycode, keyrecord_t *record) {
    cheapino_telemetry_record_post_action(keycode, record);
    post_process_record_user(keycode, record);
}

void raw_hid_receive_kb(uint8_t *data, uint8_t length) {
    if (!cheapino_telemetry_raw_hid_receive(data, length)) {
        data[0] = id_unhandled;
    }
}
