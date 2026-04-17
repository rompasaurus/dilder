/*
 * main.cpp -- Dilder ESP32-S3 Firmware Entry Point
 *
 * Olimex ESP32-S3-DevKit-Lipo + Waveshare 2.13" e-Paper V3 + 5-way joystick.
 *
 * This is the Arduino-framework entry point for the ESP32-S3 build.
 * It initializes the HAL, runs the e-Paper display test, and enters
 * the main loop reading joystick input and updating the display.
 */

#include <Arduino.h>
#include <SPI.h>

/* GxEPD2 — e-Paper display driver for Waveshare 2.13" V3 (SSD1680) */
#include <GxEPD2_BW.h>
#include <Adafruit_GFX.h>

/* Shared firmware headers */
extern "C" {
#include "platform/board_config.h"
#include "platform/hal.h"
}

/* ── Display setup ─────────────────────────────────────────────────── */

/* Waveshare 2.13" V3 = SSD1680, 250x122 pixels
 * GxEPD2 class: GxEPD2_213_BN (for V3/SSD1680)
 * Constructor: (CS, DC, RST, BUSY) */
GxEPD2_BW<GxEPD2_213_BN, GxEPD2_213_BN::HEIGHT>
    display(GxEPD2_213_BN(PIN_EPD_CS, PIN_EPD_DC, PIN_EPD_RST, PIN_EPD_BUSY));

/* ── Forward declarations ──────────────────────────────────────────── */
void draw_startup_screen(void);
void draw_chip_info(void);
void handle_joystick(void);

/* ── Setup ─────────────────────────────────────────────────────────── */

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n=== Dilder ESP32-S3 Firmware ===");
    Serial.printf("Board: %s\n", BOARD_NAME);
    Serial.printf("Flash: %d KB\n", BOARD_FLASH_KB);
    Serial.printf("PSRAM: %lu bytes\n", ESP.getPsramSize());

    /* Initialize HAL (joystick pull-ups, LED, ADC) */
    dilder_hal_init();

    /* Initialize SPI for the display on FSPI pins */
    SPI.begin(PIN_EPD_CLK, -1 /* MISO unused */, PIN_EPD_DIN, PIN_EPD_CS);

    /* Initialize the e-Paper display */
    display.init(115200, true, 2, false);  /* serial diag, initial=true, reset_duration=2 */
    display.setRotation(1);                /* landscape orientation */
    display.setTextColor(GxEPD_BLACK);
    display.setTextSize(1);

    /* Show startup screen */
    draw_startup_screen();

    Serial.println("Setup complete. Entering main loop.");
    Serial.println("Joystick: UP/DOWN/LEFT/RIGHT/CENTER");
}

/* ── Main loop ─────────────────────────────────────────────────────── */

void loop() {
    handle_joystick();
    delay(50);  /* 20 Hz polling */
}

/* ── Display functions ─────────────────────────────────────────────── */

void draw_startup_screen(void) {
    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);

        /* Title */
        display.setCursor(10, 10);
        display.setTextSize(2);
        display.print("DILDER");

        display.setTextSize(1);
        display.setCursor(10, 35);
        display.print("ESP32-S3 Olimex DevKit-Lipo");

        /* Divider line */
        display.drawLine(10, 48, 240, 48, GxEPD_BLACK);

        /* Board info */
        display.setCursor(10, 55);
        display.printf("PSRAM: %lu KB", ESP.getPsramSize() / 1024);

        display.setCursor(10, 68);
        float bat = hal_battery_voltage();
        display.printf("Battery: %.2fV", bat);

        display.setCursor(10, 81);
        display.printf("USB: %s", hal_usb_power_connected() ? "connected" : "battery");

        /* Joystick hint */
        display.setCursor(10, 100);
        display.print("Press joystick to test...");

    } while (display.nextPage());

    hal_led_on();
    delay(200);
    hal_led_off();
}

void draw_chip_info(void) {
    display.setFullWindow();
    display.firstPage();
    do {
        display.fillScreen(GxEPD_WHITE);
        display.setTextSize(1);

        display.setCursor(10, 10);
        display.printf("Chip: %s rev %d", ESP.getChipModel(), ESP.getChipRevision());

        display.setCursor(10, 23);
        display.printf("Cores: %d  Freq: %d MHz", ESP.getChipCores(), ESP.getCpuFreqMHz());

        display.setCursor(10, 36);
        display.printf("Flash: %d KB", ESP.getFlashChipSize() / 1024);

        display.setCursor(10, 49);
        display.printf("PSRAM: %lu KB", ESP.getPsramSize() / 1024);

        display.setCursor(10, 62);
        display.printf("Free heap: %lu KB", ESP.getFreeHeap() / 1024);

        display.setCursor(10, 75);
        display.printf("SDK: %s", ESP.getSdkVersion());

        display.setCursor(10, 95);
        float bat = hal_battery_voltage();
        display.printf("Battery: %.2fV  USB: %s", bat,
                       hal_usb_power_connected() ? "yes" : "no");

        display.setCursor(10, 110);
        display.print("CENTER = back to main");

    } while (display.nextPage());
}

/* ── Joystick handling ─────────────────────────────────────────────── */

static bool last_up = false, last_down = false, last_left = false,
            last_right = false, last_center = false;

void handle_joystick(void) {
    bool up     = hal_btn_up();
    bool down   = hal_btn_down();
    bool left   = hal_btn_left();
    bool right  = hal_btn_right();
    bool center = hal_btn_center();

    /* Detect rising edges (button just pressed) */
    if (up && !last_up) {
        Serial.println("Joystick: UP");
        hal_led_on(); delay(100); hal_led_off();
    }
    if (down && !last_down) {
        Serial.println("Joystick: DOWN");
        hal_led_on(); delay(100); hal_led_off();
    }
    if (left && !last_left) {
        Serial.println("Joystick: LEFT");
        hal_led_on(); delay(100); hal_led_off();
    }
    if (right && !last_right) {
        Serial.println("Joystick: RIGHT");
        hal_led_on(); delay(100); hal_led_off();
    }
    if (center && !last_center) {
        Serial.println("Joystick: CENTER — showing chip info");
        draw_chip_info();
    }

    last_up = up; last_down = down; last_left = left;
    last_right = right; last_center = center;
}
