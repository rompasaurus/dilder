/*
 * hal.h -- Hardware Abstraction Layer interface
 *
 * Platform-agnostic function declarations for hardware I/O.
 * Each board platform (desktop, pico_w, esp32s3) provides its own
 * implementation of these functions.
 *
 * The game engine calls these functions instead of touching hardware
 * directly, making it portable across all target boards.
 */

#ifndef HAL_H
#define HAL_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Lifecycle ─────────────────────────────────────────────────────── */

/* Initialize all board-specific hardware (SPI, GPIO, ADC, etc.) */
void dilder_hal_init(void);

/* ── SPI / Display ─────────────────────────────────────────────────── */

/* Write raw bytes over SPI to the e-Paper display */
void hal_spi_write(const uint8_t *data, uint16_t len);

/* Send a command byte to the display controller */
void hal_epd_cmd(uint8_t cmd);

/* Send data bytes to the display controller */
void hal_epd_data(const uint8_t *data, uint16_t len);

/* Hardware-reset the display (pulse RST pin LOW) */
void hal_epd_reset(void);

/* Returns 1 if the display BUSY pin is HIGH (display is busy) */
int hal_epd_busy(void);

/* ── Buttons / Joystick ────────────────────────────────────────────── */

/* Each returns 1 if the button is currently pressed, 0 otherwise */
int hal_btn_up(void);
int hal_btn_down(void);
int hal_btn_left(void);
int hal_btn_right(void);
int hal_btn_center(void);

/* ── LED ───────────────────────────────────────────────────────────── */

void hal_led_on(void);
void hal_led_off(void);

/* ── Battery (ESP32-S3 only, stubs on other platforms) ─────────────── */

/* Returns battery voltage in volts (e.g. 3.7) */
float hal_battery_voltage(void);

/* Returns 1 if USB power is connected */
int hal_usb_power_connected(void);

/* ── Timing ────────────────────────────────────────────────────────── */

uint32_t hal_millis(void);
void hal_delay_ms(uint32_t ms);

#ifdef __cplusplus
}
#endif

#endif /* HAL_H */
