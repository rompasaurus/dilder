/*
 * board_config.h -- Compile-time board selection and pin definitions
 *
 * Provides a unified set of pin/peripheral macros that abstract over the
 * target hardware.  Each board defines the same macro names so the game
 * engine and display driver can use them without #ifdef everywhere.
 *
 * Currently supported boards:
 *   - BOARD_PICO_W       Raspberry Pi Pico W  (RP2040, SPI1)
 *   - BOARD_ESP32S3      Olimex ESP32-S3-DevKit-Lipo  (ESP32-S3, FSPI)
 *
 * Set the target board at build time:
 *   cmake  -DTARGET_BOARD=PICO_W ..
 *   cmake  -DTARGET_BOARD=ESP32S3 ..
 * Or in platformio.ini:
 *   build_flags = -DBOARD_ESP32S3
 */

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

/* ================================================================
 *  Pico W  (RP2040)
 * ================================================================ */
#if defined(BOARD_PICO_W) || defined(PICO_BOARD)

#define BOARD_NAME          "Pico W"

/* e-Paper display — SPI1 */
#define PIN_EPD_CLK         10   /* GP10  SPI1 SCK   pin 14 */
#define PIN_EPD_DIN         11   /* GP11  SPI1 TX    pin 15 */
#define PIN_EPD_CS           9   /* GP9              pin 12 */
#define PIN_EPD_DC           8   /* GP8              pin 11 */
#define PIN_EPD_RST         12   /* GP12             pin 16 */
#define PIN_EPD_BUSY        13   /* GP13             pin 17 */

/* 5-way joystick / buttons */
#define PIN_BTN_UP           2   /* GP2   pin 4  */
#define PIN_BTN_DOWN         3   /* GP3   pin 5  */
#define PIN_BTN_LEFT         4   /* GP4   pin 6  */
#define PIN_BTN_RIGHT        5   /* GP5   pin 7  */
#define PIN_BTN_CENTER       6   /* GP6   pin 9  */

/* SPI controller */
#define EPD_SPI_CONTROLLER   1   /* SPI1 */
#define EPD_SPI_FREQ_HZ      4000000  /* 4 MHz */

/* Flash size */
#define BOARD_FLASH_KB       2048  /* 2 MB */

/* ================================================================
 *  Olimex ESP32-S3-DevKit-Lipo
 * ================================================================ */
#elif defined(BOARD_ESP32S3)

#define BOARD_NAME          "ESP32-S3 (Olimex)"

/* e-Paper display — FSPI (SPI3) on pUEXT pins */
#define PIN_EPD_CLK         12   /* GPIO12  FSPI CLK   EXT1-18 */
#define PIN_EPD_DIN         11   /* GPIO11  FSPI MOSI  EXT1-17 */
#define PIN_EPD_CS          10   /* GPIO10  FSPI CS    EXT1-16 (10k pull-up) */
#define PIN_EPD_DC           9   /* GPIO9             EXT1-15 */
#define PIN_EPD_RST          3   /* GPIO3  (strapping, safe after boot) EXT1-13 */
#define PIN_EPD_BUSY         8   /* GPIO8             EXT1-12 */

/* 5-way joystick */
#define PIN_BTN_UP           4   /* GPIO4   EXT1-4  */
#define PIN_BTN_DOWN         7   /* GPIO7   EXT1-7  */
#define PIN_BTN_LEFT         1   /* GPIO1   EXT2-4  */
#define PIN_BTN_RIGHT        2   /* GPIO2   EXT2-5  */
#define PIN_BTN_CENTER      15   /* GPIO15  EXT1-8  */

/* SPI controller */
#define EPD_SPI_CONTROLLER   3   /* FSPI (SPI3) */
#define EPD_SPI_FREQ_HZ      4000000  /* 4 MHz */

/* On-board peripherals */
#define PIN_LED             38   /* Green LED, active LOW */
#define PIN_BAT_ADC          6   /* Battery voltage sense (÷4.133) */
#define PIN_PWR_ADC          5   /* USB power detect (÷1.468) */
#define PIN_BOOT_BTN         0   /* BOOT button (usable as user button) */

/* I2C — reserved for future sensors (pull-ups on board) */
#define PIN_I2C_SDA         48   /* GPIO48  EXT2-16 */
#define PIN_I2C_SCL         47   /* GPIO47  EXT2-17 */

/* Flash size */
#define BOARD_FLASH_KB       8192  /* 8 MB */

/* ================================================================
 *  Desktop / Simulation  (no real pins)
 * ================================================================ */
#elif defined(BOARD_DESKTOP) || !defined(BOARD_PICO_W)

#define BOARD_NAME          "Desktop"

/* Dummy pin values for the desktop simulation build.
 * These are never read by real GPIO drivers — they exist so code
 * that references PIN_EPD_* macros still compiles cleanly. */
#define PIN_EPD_CLK          0
#define PIN_EPD_DIN          0
#define PIN_EPD_CS           0
#define PIN_EPD_DC           0
#define PIN_EPD_RST          0
#define PIN_EPD_BUSY         0

#define PIN_BTN_UP           0
#define PIN_BTN_DOWN         0
#define PIN_BTN_LEFT         0
#define PIN_BTN_RIGHT        0
#define PIN_BTN_CENTER       0

#define EPD_SPI_CONTROLLER   0
#define EPD_SPI_FREQ_HZ      0
#define BOARD_FLASH_KB       0

#endif /* board selection */

#endif /* BOARD_CONFIG_H */
