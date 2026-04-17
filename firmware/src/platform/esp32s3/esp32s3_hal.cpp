/*
 * esp32s3_hal.cpp -- Hardware Abstraction Layer for Olimex ESP32-S3-DevKit-Lipo
 *
 * Provides board-specific initialization for the ESP32-S3 platform:
 *   - SPI setup for the Waveshare 2.13" e-Paper display (FSPI / SPI3)
 *   - GPIO setup for the 5-way joystick (internal pull-ups)
 *   - Battery voltage ADC reading
 *   - On-board LED control
 *
 * This file is only compiled when BOARD_ESP32S3 is defined.
 * Compiled as C++ for Arduino SPI API, but exports C linkage for the
 * shared game engine.
 */

#ifdef BOARD_ESP32S3

#include "platform/board_config.h"

#ifdef ARDUINO
/* ── Arduino framework (PlatformIO default) ────────────────────────── */

#include <Arduino.h>
#include <SPI.h>

static SPIClass *epd_spi = NULL;

extern "C" {

void dilder_hal_init(void) {
    /* Joystick — all buttons are active LOW, use internal pull-ups */
    pinMode(PIN_BTN_UP,     INPUT_PULLUP);
    pinMode(PIN_BTN_DOWN,   INPUT_PULLUP);
    pinMode(PIN_BTN_LEFT,   INPUT_PULLUP);
    pinMode(PIN_BTN_RIGHT,  INPUT_PULLUP);
    pinMode(PIN_BTN_CENTER, INPUT_PULLUP);

    /* On-board LED (active LOW) */
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);  /* OFF */

    /* e-Paper control pins */
    pinMode(PIN_EPD_CS,   OUTPUT);
    pinMode(PIN_EPD_DC,   OUTPUT);
    pinMode(PIN_EPD_RST,  OUTPUT);
    pinMode(PIN_EPD_BUSY, INPUT);

    digitalWrite(PIN_EPD_CS, HIGH);  /* deselect */

    /* SPI — use FSPI (SPI3) on the pUEXT pins */
    epd_spi = new SPIClass(FSPI);
    epd_spi->begin(PIN_EPD_CLK, -1 /* MISO unused */, PIN_EPD_DIN, PIN_EPD_CS);

    /* Battery ADC */
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
}

void hal_spi_write(const uint8_t *data, uint16_t len) {
    if (!epd_spi) return;
    epd_spi->beginTransaction(SPISettings(EPD_SPI_FREQ_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(PIN_EPD_CS, LOW);
    epd_spi->transferBytes(data, NULL, len);
    digitalWrite(PIN_EPD_CS, HIGH);
    epd_spi->endTransaction();
}

void hal_epd_cmd(uint8_t cmd) {
    digitalWrite(PIN_EPD_DC, LOW);   /* command mode */
    hal_spi_write(&cmd, 1);
    digitalWrite(PIN_EPD_DC, HIGH);  /* back to data mode */
}

void hal_epd_data(const uint8_t *data, uint16_t len) {
    digitalWrite(PIN_EPD_DC, HIGH);  /* data mode */
    if (!epd_spi) return;
    epd_spi->beginTransaction(SPISettings(EPD_SPI_FREQ_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(PIN_EPD_CS, LOW);
    epd_spi->transferBytes(data, NULL, len);
    digitalWrite(PIN_EPD_CS, HIGH);
    epd_spi->endTransaction();
}

void hal_epd_reset(void) {
    digitalWrite(PIN_EPD_RST, LOW);
    delay(10);
    digitalWrite(PIN_EPD_RST, HIGH);
    delay(10);
}

int hal_epd_busy(void) {
    return digitalRead(PIN_EPD_BUSY) == HIGH;
}

/* Joystick reading — returns 1 if pressed (active LOW inverted) */
int hal_btn_up(void)     { return digitalRead(PIN_BTN_UP)     == LOW; }
int hal_btn_down(void)   { return digitalRead(PIN_BTN_DOWN)   == LOW; }
int hal_btn_left(void)   { return digitalRead(PIN_BTN_LEFT)   == LOW; }
int hal_btn_right(void)  { return digitalRead(PIN_BTN_RIGHT)  == LOW; }
int hal_btn_center(void) { return digitalRead(PIN_BTN_CENTER) == LOW; }

/* LED */
void hal_led_on(void)  { digitalWrite(PIN_LED, LOW);  }
void hal_led_off(void) { digitalWrite(PIN_LED, HIGH); }

/* Battery voltage — divider ratio 4.133 on GPIO6 */
float hal_battery_voltage(void) {
    int raw = analogRead(PIN_BAT_ADC);
    return raw * (3.3f / 4095.0f) * 4.133f;
}

/* USB power detection — divider ratio 1.468 on GPIO5 */
int hal_usb_power_connected(void) {
    int raw = analogRead(PIN_PWR_ADC);
    float voltage = raw * (3.3f / 4095.0f) * 1.468f;
    return voltage > 3.0f;  /* USB 5V through divider reads ~3.4V */
}

uint32_t hal_millis(void) {
    return millis();
}

void hal_delay_ms(uint32_t ms) {
    delay(ms);
}

} /* extern "C" */

#endif /* ARDUINO */
#endif /* BOARD_ESP32S3 */
