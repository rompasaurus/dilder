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

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What is this file doing?
 * --------------------------------------------------------------------------
 *
 *  Different boards have their components wired to different GPIO pins.
 *  For example, the e-Paper display clock wire is connected to:
 *    - GPIO 10 on the Pico W
 *    - GPIO 12 on the ESP32-S3
 *
 *  Instead of scattering these pin numbers throughout the codebase
 *  (which would make switching boards a nightmare), we define them
 *  all HERE using #define macros with consistent names.
 *
 *  The rest of the code just uses PIN_EPD_CLK everywhere.  This file
 *  ensures PIN_EPD_CLK expands to the right number for whichever board
 *  we're building for.
 *
 *  Think of it like a wiring diagram in code form: "On this board,
 *  the clock wire goes to pin 12, the data wire goes to pin 11, ..."
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: #if defined() / #elif / #else preprocessor chains
 * --------------------------------------------------------------------------
 *
 *  The C preprocessor can make decisions at COMPILE TIME using conditional
 *  directives.  This is different from if/else in regular code, which
 *  makes decisions at RUN TIME.
 *
 *  Preprocessor conditionals actually REMOVE code from the source before
 *  the compiler sees it.  Only the branch that matches gets compiled.
 *  The other branches are thrown away entirely.
 *
 *  Here's the pattern used in this file:
 *
 *    #if defined(BOARD_PICO_W)        // Is BOARD_PICO_W defined?
 *      ... Pico W pin definitions ... // YES: use these
 *
 *    #elif defined(BOARD_ESP32S3)     // Otherwise, is BOARD_ESP32S3 defined?
 *      ... ESP32-S3 pin definitions . // YES: use these
 *
 *    #else                            // Neither was defined
 *      ... Desktop dummy values ..... // Use these as fallback
 *
 *    #endif                           // End of the conditional chain
 *
 *  "defined(X)" returns true if the symbol X has been #defined, either
 *  in code or via a compiler flag like -DBOARD_ESP32S3.
 *
 *  This is like a switch statement, but it happens before compilation.
 *  Only ONE set of pin definitions ends up in the compiled binary.
 *
 *  You can also use #ifdef X as shorthand for #if defined(X), but
 *  #if defined() is more flexible because you can combine conditions:
 *    #if defined(BOARD_PICO_W) || defined(PICO_BOARD)
 *  This means "if either BOARD_PICO_W or PICO_BOARD is defined."
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: BOARD_NAME, BOARD_FLASH_KB, and other constants
 * --------------------------------------------------------------------------
 *
 *  Besides pin numbers, each board section defines:
 *
 *  BOARD_NAME — A human-readable string like "Pico W" or "ESP32-S3 (Olimex)".
 *    Used in log messages, status displays, etc.  It doesn't affect
 *    hardware behavior — it's just for humans reading debug output.
 *
 *  BOARD_FLASH_KB — The amount of flash memory (in kilobytes) on the board.
 *    The Pico W has 2 MB (2048 KB), the ESP32-S3 has 8 MB (8192 KB).
 *    This could be used to adjust how much data we store (save files,
 *    game assets, etc.) based on available space.
 *
 *  EPD_SPI_CONTROLLER — Which SPI hardware block to use (see below).
 *
 *  EPD_SPI_FREQ_HZ — The SPI clock speed in Hertz.  4,000,000 = 4 MHz,
 *    meaning 4 million clock pulses per second.  The e-Paper display
 *    datasheet specifies the maximum safe speed.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: SPI bus selection (SPI0 / SPI1 / FSPI / HSPI)
 * --------------------------------------------------------------------------
 *
 *  Microcontrollers have multiple SPI controllers (hardware blocks that
 *  can each independently run an SPI bus).  You can't just use any of
 *  them — some are reserved:
 *
 *  ESP32-S3 SPI controllers:
 *    SPI0, SPI1 — RESERVED by the chip for accessing the internal flash
 *                 memory.  If you used these, you'd interfere with reading
 *                 your own firmware code.  Never use these for peripherals.
 *    FSPI (SPI3) — "Fast SPI" — the first GENERAL PURPOSE SPI controller.
 *                  This is what we use for the e-Paper display.
 *    HSPI (SPI2) — Another general-purpose SPI controller.  Available if
 *                  you need a second SPI bus for another device.
 *
 *  RP2040 (Pico W) SPI controllers:
 *    SPI0 — General purpose (both are usable on this chip).
 *    SPI1 — General purpose.  We use SPI1 for the display because
 *           the chosen GPIO pins happen to be on SPI1's pin mux.
 *
 *  The EPD_SPI_CONTROLLER macro tells the HAL code which controller
 *  number to use when initializing the SPI bus.
 * --------------------------------------------------------------------------
 */

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

/* ================================================================
 *  Pico W  (RP2040)
 * ================================================================
 *
 * #if defined(BOARD_PICO_W) || defined(PICO_BOARD)
 *
 * This checks for EITHER of two symbols:
 *   - BOARD_PICO_W: our own build flag, set manually
 *   - PICO_BOARD: automatically defined by the Pico SDK
 *
 * The "||" means "or" — if either symbol is defined, we enter
 * this branch.  This way the right pins are selected whether
 * you use our build system or the Pico SDK's default setup.
 */
#if defined(BOARD_PICO_W) || defined(PICO_BOARD)

#define BOARD_NAME          "Pico W"

/*
 * e-Paper display — SPI1
 *
 * Each #define creates a macro that the preprocessor replaces
 * throughout the code.  For example, everywhere the code says
 * PIN_EPD_CLK, the preprocessor substitutes the number 10.
 *
 * The comments show: GPIO number, SPI function, physical pin on
 * the Pico W board header.  "GP10" means GPIO pin 10, which is
 * physical pin 14 on the board's 40-pin header.
 */
#define PIN_EPD_CLK         10   /* GP10  SPI1 SCK   pin 14 */
#define PIN_EPD_DIN         11   /* GP11  SPI1 TX    pin 15 */
#define PIN_EPD_CS           9   /* GP9              pin 12 */
#define PIN_EPD_DC           8   /* GP8              pin 11 */
#define PIN_EPD_RST         12   /* GP12             pin 16 */
#define PIN_EPD_BUSY        13   /* GP13             pin 17 */

/* 5-way joystick / buttons
 *
 * Each button gets its own GPIO pin.  The physical wiring
 * connects one side of the button to the GPIO and the other
 * side to GND.  When pressed, the pin gets pulled LOW.
 */
#define PIN_BTN_UP           2   /* GP2   pin 4  */
#define PIN_BTN_DOWN         3   /* GP3   pin 5  */
#define PIN_BTN_LEFT         4   /* GP4   pin 6  */
#define PIN_BTN_RIGHT        5   /* GP5   pin 7  */
#define PIN_BTN_CENTER       6   /* GP6   pin 9  */

/* SPI controller selection.
 * On the Pico W, we use SPI1 (the second SPI controller).
 * SPI0 is also available but we chose SPI1 based on which
 * GPIO pins we're using (each SPI controller can only use
 * certain pin groups due to the RP2040's pin multiplexing). */
#define EPD_SPI_CONTROLLER   1   /* SPI1 */
#define EPD_SPI_FREQ_HZ      4000000  /* 4 MHz */

/* Flash size — the Pico W has 2 MB of onboard flash storage.
 * This is where the firmware binary and any saved data live. */
#define BOARD_FLASH_KB       2048  /* 2 MB */

/* ================================================================
 *  Olimex ESP32-S3-DevKit-Lipo
 * ================================================================
 *
 * #elif defined(BOARD_ESP32S3)
 *
 * #elif is "else if" for the preprocessor.  We only reach here if
 * the BOARD_PICO_W check above was false (i.e., we're not building
 * for the Pico W).  Then we check: is BOARD_ESP32S3 defined?
 */
#elif defined(BOARD_ESP32S3)

#define BOARD_NAME          "ESP32-S3 (Olimex)"

/*
 * e-Paper display — FSPI (SPI3) on pUEXT connector pins.
 *
 * The Olimex board has a "pUEXT" connector — a standardized pinout
 * for connecting peripherals.  We wire the e-Paper display to these
 * pins.  The EXT1-XX comments refer to pin numbers on the pUEXT
 * connector (not the GPIO numbers — those are the #define values).
 *
 * Note: GPIO10 has a 10k pull-up resistor on the board, which is
 * fine for a chip-select line (CS idles HIGH anyway).
 */
#define PIN_EPD_CLK         12   /* GPIO12  FSPI CLK   EXT1-18 */
#define PIN_EPD_DIN         11   /* GPIO11  FSPI MOSI  EXT1-17 */
#define PIN_EPD_CS          10   /* GPIO10  FSPI CS    EXT1-16 (10k pull-up) */
#define PIN_EPD_DC           9   /* GPIO9             EXT1-15 */
#define PIN_EPD_RST          3   /* GPIO3  (strapping, safe after boot) EXT1-13 */
#define PIN_EPD_BUSY         8   /* GPIO8             EXT1-12 */

/* 5-way joystick — spread across EXT1 and EXT2 connectors */
#define PIN_BTN_UP           4   /* GPIO4   EXT1-4  */
#define PIN_BTN_DOWN         7   /* GPIO7   EXT1-7  */
#define PIN_BTN_LEFT         1   /* GPIO1   EXT2-4  */
#define PIN_BTN_RIGHT        2   /* GPIO2   EXT2-5  */
#define PIN_BTN_CENTER      15   /* GPIO15  EXT1-8  */

/*
 * SPI controller — FSPI (SPI3).
 *
 * We use FSPI (controller #3) because SPI0 and SPI1 on the ESP32-S3
 * are reserved for internal flash access.  See the SPI bus selection
 * notes at the top of this file for more details.
 */
#define EPD_SPI_CONTROLLER   3   /* FSPI (SPI3) */
#define EPD_SPI_FREQ_HZ      4000000  /* 4 MHz */

/*
 * On-board peripherals — these are built into the Olimex board,
 * not external add-ons.
 *
 * PIN_LED — The board has a green LED.  It's "active LOW," meaning
 *   you turn it ON by driving the pin LOW (see esp32s3_hal.cpp).
 *
 * PIN_BAT_ADC — Connected to the battery through a voltage divider
 *   (ratio 4.133:1).  We read this with analogRead() to calculate
 *   the battery voltage.
 *
 * PIN_PWR_ADC — Connected to the USB 5V power rail through a voltage
 *   divider (ratio 1.468:1).  We read this to detect if USB is plugged in.
 *
 * PIN_BOOT_BTN — The BOOT button is normally used to put the ESP32 into
 *   firmware download mode, but after boot it's usable as a regular
 *   user button (active LOW, with an external pull-up on the board).
 */
#define PIN_LED             38   /* Green LED, active LOW */
#define PIN_BAT_ADC          6   /* Battery voltage sense (divider ratio 4.133) */
#define PIN_PWR_ADC          5   /* USB power detect (divider ratio 1.468) */
#define PIN_BOOT_BTN         0   /* BOOT button (usable as user button) */

/*
 * I2C bus pins — reserved for future sensors.
 *
 * I2C (Inter-Integrated Circuit) is another communication protocol,
 * simpler than SPI: it uses just 2 wires (SDA for data, SCL for clock)
 * and can connect multiple devices on the same bus.  Each device has
 * a unique address.
 *
 * These pins have pull-up resistors on the Olimex board, which I2C
 * requires.  They're defined here for future use (e.g., temperature
 * sensor, light sensor) but nothing uses them yet.
 */
#define PIN_I2C_SDA         48   /* GPIO48  EXT2-16 */
#define PIN_I2C_SCL         47   /* GPIO47  EXT2-17 */

/* Flash size — the Olimex ESP32-S3 board has 8 MB of flash.
 * That's 4x more than the Pico W, giving us plenty of room
 * for game assets and save data. */
#define BOARD_FLASH_KB       8192  /* 8 MB */

/* ================================================================
 *  Desktop / Simulation  (no real pins)
 * ================================================================
 *
 * #elif defined(BOARD_DESKTOP) || !defined(BOARD_PICO_W)
 *
 * This is the fallback.  It activates if:
 *   - BOARD_DESKTOP is explicitly defined, OR
 *   - Neither BOARD_PICO_W nor BOARD_ESP32S3 was defined
 *     (catches the case where someone builds without setting a board)
 *
 * The "!" means "not" — so !defined(BOARD_PICO_W) is true when
 * BOARD_PICO_W is NOT defined.
 */
#elif defined(BOARD_DESKTOP) || !defined(BOARD_PICO_W)

#define BOARD_NAME          "Desktop"

/*
 * Dummy pin values for the desktop simulation build.
 *
 * These are all set to 0 because there are no real GPIO pins on a
 * desktop PC.  They exist solely so code that references PIN_EPD_*
 * macros still compiles without errors.
 *
 * The desktop HAL implementation (desktop_hal.c) doesn't actually
 * call digitalRead() or analogRead() — it uses SDL or similar
 * libraries to simulate the hardware.  So these pin numbers are
 * never used for real I/O; they just keep the compiler happy.
 */
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
