#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "matrix.h"
#include "protocol.h"
#include "telemetry.h"

layer_state_t layer_state = 1u;
layer_state_t default_layer_state = 1u;

static matrix_row_t fake_matrix[MATRIX_ROWS];
static uint32_t fake_time = 1000u;
static uint8_t fake_mods;

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
void matrix_scan_user(void) {}
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    (void)keycode;
    (void)record;
    return true;
}
void post_process_record_user(uint16_t keycode, keyrecord_t *record) {
    (void)keycode;
    (void)record;
}

static bool read_exact(uint8_t *buffer, size_t size) {
    size_t offset = 0;
    while (offset < size) {
        const size_t n = fread(buffer + offset, 1, size - offset, stdin);
        if (n == 0) {
            return false;
        }
        offset += n;
    }
    return true;
}

int main(void) {
    uint8_t report[CHEAPINO_TELEMETRY_REPORT_SIZE];

    while (read_exact(report, sizeof(report))) {
        raw_hid_receive_kb(report, sizeof(report));
        if (fwrite(report, 1, sizeof(report), stdout) != sizeof(report)) {
            return 2;
        }
        if (fflush(stdout) != 0) {
            return 3;
        }
    }
    return ferror(stdin) ? 1 : 0;
}
