#ifndef DILDER_SENSOR_H
#define DILDER_SENSOR_H

#include "game/game_state.h"

/* ─── Sensor Manager API ─────────────────────────────────────── */

void sensor_init(void);

/* Poll all sensors (uses emulated values in desktop mode) */
sensor_context_t sensor_poll(uint32_t now_ms);

/* Classify sensor changes into game events */
void sensor_classify_events(const sensor_context_t *prev,
                            const sensor_context_t *curr);

/* ─── Emulation API (desktop only) ───────────────────────────── */

/* Set individual sensor values from the DevTool */
void sensor_emu_set_light(float lux);
void sensor_emu_set_temperature(float celsius);
void sensor_emu_set_humidity(float percent);
void sensor_emu_set_mic_level(uint16_t level);
void sensor_emu_set_steps(uint32_t step_count);
void sensor_emu_set_accel(int16_t x, int16_t y, int16_t z);
void sensor_emu_set_shaking(bool shaking);
void sensor_emu_set_walking(bool walking);
void sensor_emu_set_at_home(bool at_home);

#endif /* DILDER_SENSOR_H */
