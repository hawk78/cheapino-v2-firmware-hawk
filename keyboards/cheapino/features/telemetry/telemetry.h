#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "quantum.h"

void cheapino_telemetry_scan_matrix(void);
void cheapino_telemetry_record_resolved(uint16_t keycode, keyrecord_t *record);
void cheapino_telemetry_record_post_action(uint16_t keycode, keyrecord_t *record);
bool cheapino_telemetry_raw_hid_receive(uint8_t *data, uint8_t length);
