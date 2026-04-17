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

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What is a Hardware Abstraction Layer (HAL)?
 * --------------------------------------------------------------------------
 *
 *  A HAL is a design pattern that separates "what to do" from "how to do it
 *  on this specific chip."
 *
 *  Imagine you're writing a game that needs to read a button.  On the
 *  ESP32-S3, you'd call digitalRead(4).  On the Pico W, you'd call
 *  gpio_get(2).  On a desktop PC, you'd check SDL keyboard events.
 *
 *  If the game code had all three versions mixed in with #ifdefs, it
 *  would become an unreadable mess.  The HAL solves this:
 *
 *  1. This header (hal.h) declares a simple, universal API:
 *         int hal_btn_up(void);     // "is the UP button pressed?"
 *
 *  2. Each platform provides its OWN implementation of that function:
 *         esp32s3_hal.cpp  -->  uses digitalRead()
 *         pico_w_hal.c     -->  uses gpio_get()
 *         desktop_hal.c    -->  uses SDL_GetKeyboardState()
 *
 *  3. The game engine only #includes hal.h and calls hal_btn_up().
 *     It doesn't know or care which chip is underneath.
 *
 *  This is called "programming to an interface" — one of the most useful
 *  patterns in software engineering.  The game engine depends on the
 *  INTERFACE (hal.h), not the IMPLEMENTATION (esp32s3_hal.cpp).
 *
 *  To add a new board, you just write a new hal implementation file
 *  that provides all the functions declared here.  The game engine
 *  code doesn't change at all.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: What are #ifndef / #define / #endif "include guards"?
 * --------------------------------------------------------------------------
 *
 *  When the C preprocessor sees #include "hal.h", it literally copy-pastes
 *  the entire contents of hal.h into your .c file.  If multiple files
 *  #include "hal.h" (or one file includes it indirectly through two
 *  different headers), the declarations would appear TWICE, causing
 *  "duplicate definition" compiler errors.
 *
 *  Include guards prevent this:
 *
 *    #ifndef HAL_H       // "if HAL_H is NOT yet defined..."
 *    #define HAL_H       // "...define it now (so next time we skip)"
 *      ... all the declarations ...
 *    #endif              // "end of the conditional block"
 *
 *  The FIRST time hal.h is included, HAL_H is not defined, so the
 *  preprocessor enters the block, defines HAL_H, and includes all
 *  the declarations.
 *
 *  The SECOND time hal.h is included (in the same compilation unit),
 *  HAL_H is already defined, so #ifndef is false, and the preprocessor
 *  skips everything.  No duplicate declarations.
 *
 *  The name "HAL_H" is just a convention: uppercase filename with
 *  underscores replacing dots and slashes.  It can be anything unique,
 *  but matching the filename makes it easy to find.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: Function declarations (prototypes) vs. definitions
 * --------------------------------------------------------------------------
 *
 *  A function DECLARATION (also called a "prototype") tells the compiler:
 *    "This function exists, here's its name, what it takes, and what it
 *     returns — but I'm not giving you the code body yet."
 *
 *    Example:  int hal_btn_up(void);    <-- declaration (ends with ;)
 *
 *  A function DEFINITION provides the actual code:
 *
 *    Example:  int hal_btn_up(void) {   <-- definition (has a body)
 *                return digitalRead(PIN_BTN_UP) == LOW;
 *              }
 *
 *  This header file contains only DECLARATIONS.  The definitions live in
 *  the platform-specific .c/.cpp files (like esp32s3_hal.cpp).
 *
 *  Why separate them?  Because the game engine needs to know what
 *  functions it can call (declarations) without caring how they work
 *  (definitions).  The linker connects calls to definitions at build time.
 *
 *  Analogy: a restaurant menu (declarations) tells you what dishes are
 *  available.  The kitchen (definitions) is where the food actually
 *  gets made.  You only need the menu to order.
 * --------------------------------------------------------------------------
 */

/*
 * --------------------------------------------------------------------------
 *  BEGINNER NOTES: Why does hal.h use extern "C"?
 * --------------------------------------------------------------------------
 *
 *  C++ "mangles" function names to support features like overloading.
 *  For example, hal_btn_up() might become _Z10hal_btn_upv in the compiled
 *  binary.  But C doesn't mangle names — it keeps them exactly as written.
 *
 *  If hal.h is #included from a C++ file (.cpp), the compiler would
 *  mangle these function names.  But the implementations might be in a
 *  plain C file (.c), or might be declared with extern "C" in a .cpp
 *  file.  Either way, the names in the compiled code would NOT match,
 *  and the linker would fail with "undefined reference" errors.
 *
 *  The solution:
 *
 *    #ifdef __cplusplus        // "__cplusplus" is auto-defined by C++ compilers
 *    extern "C" {              // "use C naming for everything in this block"
 *    #endif
 *
 *      ... function declarations ...
 *
 *    #ifdef __cplusplus
 *    }
 *    #endif
 *
 *  When compiled as C:
 *    __cplusplus is NOT defined, so the extern "C" lines are skipped.
 *    (C doesn't even understand extern "C" — it would be a syntax error.)
 *    The declarations are compiled with C naming, as normal.
 *
 *  When compiled as C++:
 *    __cplusplus IS defined, so extern "C" { } wraps the declarations.
 *    The C++ compiler uses C-compatible (unmangled) names for them.
 *
 *  Result: whether this header is included from .c or .cpp files, the
 *  function names match, and the linker can connect everything correctly.
 * --------------------------------------------------------------------------
 */

#ifndef HAL_H
#define HAL_H

/*
 * <stdint.h> provides fixed-size integer types like uint8_t, uint16_t,
 * and uint32_t.  These guarantee an exact size regardless of platform:
 *   uint8_t  = always  8 bits (1 byte),  range 0-255
 *   uint16_t = always 16 bits (2 bytes), range 0-65535
 *   uint32_t = always 32 bits (4 bytes), range 0-4294967295
 *
 * Regular "int" might be 16 bits on one chip and 32 bits on another,
 * which can cause subtle bugs.  In embedded/hardware code, we prefer
 * the fixed-size types so we know exactly what we're getting.
 */
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Lifecycle ─────────────────────────────────────────────────────── */

/* Initialize all board-specific hardware (SPI, GPIO, ADC, etc.)
 *
 * Must be called once at startup before any other hal_* function.
 * Each platform's implementation sets up its own pins, buses, etc.
 */
void dilder_hal_init(void);

/* ── SPI / Display ─────────────────────────────────────────────────── */

/* Write raw bytes over SPI to the e-Paper display.
 *
 * Parameters:
 *   data — pointer to the byte array to send
 *   len  — how many bytes to send
 *
 * "const uint8_t *data" means: data is a pointer to bytes that this
 * function promises not to modify (that's what "const" means here).
 */
void hal_spi_write(const uint8_t *data, uint16_t len);

/* Send a command byte to the display controller.
 * Pulls DC LOW before sending so the display knows it's a command. */
void hal_epd_cmd(uint8_t cmd);

/* Send data bytes to the display controller.
 * Keeps DC HIGH so the display knows these are data, not commands. */
void hal_epd_data(const uint8_t *data, uint16_t len);

/* Hardware-reset the display (pulse RST pin LOW then back HIGH). */
void hal_epd_reset(void);

/* Returns 1 if the display BUSY pin is HIGH (display is busy).
 * Returns 0 if the display is ready to accept new commands. */
int hal_epd_busy(void);

/* ── Buttons / Joystick ────────────────────────────────────────────── */

/* Each returns 1 if the button is currently pressed, 0 otherwise.
 *
 * Note: the return type is "int" rather than "bool" because this is
 * a C interface (not C++), and C89 doesn't have a built-in bool type.
 * In C, 0 means false and any non-zero value means true.
 */
int hal_btn_up(void);
int hal_btn_down(void);
int hal_btn_left(void);
int hal_btn_right(void);
int hal_btn_center(void);

/* ── LED ───────────────────────────────────────────────────────────── */

void hal_led_on(void);
void hal_led_off(void);

/* ── Battery (ESP32-S3 only, stubs on other platforms) ─────────────── */

/* Returns battery voltage in volts (e.g. 3.7).
 *
 * On platforms without a battery ADC (like the Pico W or Desktop),
 * the implementation returns a dummy value like 0.0.  These are
 * called "stubs" — placeholder functions that satisfy the linker
 * but don't do any real work.
 */
float hal_battery_voltage(void);

/* Returns 1 if USB power is connected, 0 otherwise.
 * On platforms without USB power detection, always returns 0. */
int hal_usb_power_connected(void);

/* ── Timing ────────────────────────────────────────────────────────── */

/* Returns the number of milliseconds since the board powered on.
 * Wraps around to 0 after ~49.7 days (2^32 milliseconds). */
uint32_t hal_millis(void);

/* Pauses execution for the specified number of milliseconds.
 * WARNING: this blocks the entire CPU — no other code runs during
 * the delay.  Use sparingly; prefer non-blocking timing patterns
 * (checking hal_millis() in your main loop) for long waits. */
void hal_delay_ms(uint32_t ms);

#ifdef __cplusplus
}
#endif

#endif /* HAL_H */
