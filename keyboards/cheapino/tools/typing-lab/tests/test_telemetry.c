#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "matrix.h"
#include "protocol.h"
#include "telemetry.h"
#include "via.h"

layer_state_t layer_state = 1u;
layer_state_t default_layer_state = 1u;

static matrix_row_t fake_matrix[MATRIX_ROWS];
static uint32_t fake_time;
static uint8_t fake_mods;
static unsigned matrix_user_calls;
static unsigned process_user_calls;
static unsigned post_user_calls;

uint8_t get_highest_layer(layer_state_t state) {
    uint8_t highest = 0;
    while (state >>= 1u) {
        highest++;
    }
    return highest;
}

uint8_t get_mods(void) { return fake_mods; }
matrix_row_t matrix_get_row(uint8_t row) { return fake_matrix[row]; }
uint32_t timer_read32(void) { return fake_time++; }
void matrix_scan_user(void) { matrix_user_calls++; }
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    (void)keycode;
    (void)record;
    process_user_calls++;
    return true;
}
void post_process_record_user(uint16_t keycode, keyrecord_t *record) {
    (void)keycode;
    (void)record;
    post_user_calls++;
}

static void command(uint8_t report[CHEAPINO_TELEMETRY_REPORT_SIZE], uint8_t id) {
    memset(report, 0, CHEAPINO_TELEMETRY_REPORT_SIZE);
    report[0] = id;
    raw_hid_receive_kb(report, CHEAPINO_TELEMETRY_REPORT_SIZE);
}

static cheapino_telemetry_event_v1_t event_at(const uint8_t report[CHEAPINO_TELEMETRY_REPORT_SIZE], uint8_t index) {
    cheapino_telemetry_event_v1_t event;
    memcpy(&event, &report[8 + index * CHEAPINO_TELEMETRY_EVENT_SIZE], sizeof(event));
    return event;
}

int main(void) {
    uint8_t report[CHEAPINO_TELEMETRY_REPORT_SIZE];

    for (uint8_t row = 0; row < MATRIX_ROWS; ++row) {
        for (uint8_t col = 0; col < MATRIX_COLS; ++col) {
            const uint8_t packed = cheapino_telemetry_pack_position(row, col);
            assert((packed >> 4) == row);
            assert((packed & 0x0F) == col);
        }
    }

    command(report, CHEAPINO_TELEMETRY_GET_INFO);
    assert(report[0] == CHEAPINO_TELEMETRY_GET_INFO);
    assert(report[1] == CHEAPINO_TELEMETRY_PROTOCOL_VERSION);
    assert(report[2] == CHEAPINO_TELEMETRY_EVENT_SIZE);
    assert(report[3] == CHEAPINO_TELEMETRY_EVENTS_PER_READ);
    assert(cheapino_telemetry_read_u16_le(&report[4]) == CHEAPINO_TELEMETRY_RING_CAPACITY);
    assert(report[6] == CHEAPINO_TELEMETRY_REPORT_SIZE);

    command(report, CHEAPINO_TELEMETRY_CLEAR);
    assert(cheapino_telemetry_read_u16_le(&report[4]) == 0);

    command(report, CHEAPINO_TELEMETRY_START);
    fake_matrix[7] ^= (matrix_row_t)(1u << 11);
    matrix_scan_kb();
    command(report, CHEAPINO_TELEMETRY_STATUS);
    assert(cheapino_telemetry_read_u16_le(&report[4]) == 1);

    fake_matrix[0] = (matrix_row_t)(1u << 1);
    command(report, CHEAPINO_TELEMETRY_START);
    assert(cheapino_telemetry_read_u16_le(&report[4]) == 0);
    assert(report[2] & CHEAPINO_TELEMETRY_STATUS_CAPTURING);

    fake_time = 100;
    fake_matrix[0] |= (matrix_row_t)(1u << 2);
    matrix_scan_kb();
    assert(matrix_user_calls == 2);

    command(report, CHEAPINO_TELEMETRY_READ);
    assert(report[4] == 1);
    cheapino_telemetry_event_v1_t physical = event_at(report, 0);
    assert(physical.type == CHEAPINO_TELEMETRY_EVENT_PHYSICAL);
    assert(physical.position == cheapino_telemetry_pack_position(0, 2));
    assert(physical.flags & CHEAPINO_TELEMETRY_FLAG_PRESSED);
    assert(physical.timestamp_ms == 100);

    keyrecord_t record = {
        .event = {.key = {.row = 1, .col = 3}, .pressed = true},
        .tap = {.count = 1, .interrupted = true},
    };
    fake_mods = 0x12;
    layer_state = 1u << 4;
    assert(process_record_kb(0x1234, &record));
    post_process_record_kb(0x1234, &record);
    assert(process_user_calls == 1);
    assert(post_user_calls == 1);

    command(report, CHEAPINO_TELEMETRY_READ);
    assert(report[4] == 2);
    cheapino_telemetry_event_v1_t resolved = event_at(report, 0);
    cheapino_telemetry_event_v1_t post = event_at(report, 1);
    assert(resolved.type == CHEAPINO_TELEMETRY_EVENT_RESOLVED);
    assert(resolved.value == 0x1234);
    assert(resolved.position == cheapino_telemetry_pack_position(1, 3));
    assert((resolved.flags & (CHEAPINO_TELEMETRY_FLAG_PRESSED | CHEAPINO_TELEMETRY_FLAG_TAP | CHEAPINO_TELEMETRY_FLAG_INTERRUPTED)) ==
           (CHEAPINO_TELEMETRY_FLAG_PRESSED | CHEAPINO_TELEMETRY_FLAG_TAP | CHEAPINO_TELEMETRY_FLAG_INTERRUPTED));
    assert(resolved.layer == 4);
    assert(resolved.mods == 0x12);
    assert(resolved.aux == 1);
    assert(post.type == CHEAPINO_TELEMETRY_EVENT_POST_ACTION);

    fake_matrix[3] ^= (matrix_row_t)(1u << 5);
    matrix_scan_kb();
    memset(report, 0, sizeof(report));
    report[0] = CHEAPINO_TELEMETRY_MARK;
    report[1] = 7;
    cheapino_telemetry_write_u16_le(&report[2], 0x4567);
    raw_hid_receive_kb(report, sizeof(report));
    assert(report[0] == CHEAPINO_TELEMETRY_MARK);
    command(report, CHEAPINO_TELEMETRY_READ);
    assert(report[4] == 2);
    cheapino_telemetry_event_v1_t before_marker = event_at(report, 0);
    cheapino_telemetry_event_v1_t marker = event_at(report, 1);
    assert(before_marker.type == CHEAPINO_TELEMETRY_EVENT_PHYSICAL);
    assert(marker.type == CHEAPINO_TELEMETRY_EVENT_MARKER);
    assert(marker.value == 0x4567);
    assert(marker.aux == 7);
    assert(marker.flags & CHEAPINO_TELEMETRY_FLAG_SYNTHETIC);

    command(report, CHEAPINO_TELEMETRY_STOP);
    assert(!(report[2] & CHEAPINO_TELEMETRY_STATUS_CAPTURING));
    fake_matrix[0] ^= (matrix_row_t)(1u << 3);
    matrix_scan_kb();
    command(report, CHEAPINO_TELEMETRY_READ);
    assert(report[4] == 0);

    command(report, CHEAPINO_TELEMETRY_CLEAR);
    command(report, CHEAPINO_TELEMETRY_START);
    for (unsigned i = 0; i < 20; ++i) {
        fake_matrix[2] ^= (matrix_row_t)(1u << 4);
        matrix_scan_kb();
    }
    command(report, CHEAPINO_TELEMETRY_STATUS);
    assert(cheapino_telemetry_read_u16_le(&report[4]) == CHEAPINO_TELEMETRY_RING_CAPACITY);
    assert(report[2] & CHEAPINO_TELEMETRY_STATUS_DROPPED);
    assert(report[6] == 4 && report[7] == 0 && report[8] == 0 && report[9] == 0);
    command(report, CHEAPINO_TELEMETRY_CLEAR);
    assert(!(report[2] & CHEAPINO_TELEMETRY_STATUS_DROPPED));

    memset(report, 0, sizeof(report));
    report[0] = 0x7A;
    raw_hid_receive_kb(report, sizeof(report));
    assert(report[0] == id_unhandled);

    puts("telemetry native harness: ok");
    return 0;
}
