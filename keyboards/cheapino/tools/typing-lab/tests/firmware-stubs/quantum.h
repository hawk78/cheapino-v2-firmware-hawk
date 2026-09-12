#pragma once
#include <stdbool.h>
#include <stdint.h>

#define MATRIX_ROWS 8
#define MATRIX_COLS 12

typedef uint32_t layer_state_t;
extern layer_state_t layer_state;
extern layer_state_t default_layer_state;

typedef struct {
    struct {
        struct {
            uint8_t row;
            uint8_t col;
        } key;
        bool pressed;
    } event;
    struct {
        uint8_t count;
        bool interrupted;
    } tap;
} keyrecord_t;

uint8_t get_highest_layer(layer_state_t state);
uint8_t get_mods(void);
void matrix_scan_user(void);
bool process_record_user(uint16_t keycode, keyrecord_t *record);
void post_process_record_user(uint16_t keycode, keyrecord_t *record);

void matrix_scan_kb(void);
bool process_record_kb(uint16_t keycode, keyrecord_t *record);
void post_process_record_kb(uint16_t keycode, keyrecord_t *record);
void raw_hid_receive_kb(uint8_t *data, uint8_t length);
