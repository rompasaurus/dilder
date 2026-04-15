/*
 * dilder.h -- Dilder Firmware Public Shared Library API
 *
 * PURPOSE:
 *   This header defines the COMPLETE public interface to the Dilder game
 *   engine.  It is the ONLY header that external code (the Python DevTool)
 *   needs to know about.  All internal implementation details (structs,
 *   enums, rendering, etc.) are hidden behind these simple function
 *   declarations.
 *
 * WHO USES THIS:
 *   - The Python DevTool loads the compiled shared library (.so on Linux,
 *     .dll on Windows) and calls these functions via ctypes (Python's
 *     C Foreign Function Interface).
 *   - The standalone CLI (main_desktop.c) also uses these functions.
 *
 * FFI COMPATIBILITY:
 *   Every function here deliberately uses only simple, FFI-friendly types:
 *     - int, float       (basic numeric types ctypes understands natively)
 *     - const char *      (C string pointer -- ctypes reads it as a Python string)
 *     - const uint8_t *   (byte pointer -- ctypes reads it as a byte buffer)
 *     - void              (no return value)
 *
 *   We intentionally avoid:
 *     - Structs passed by value (ctypes can handle them, but it's fragile)
 *     - Enums in the function signature (use int instead)
 *     - Pointers to complex types
 *     - C++ types (std::string, classes, templates, etc.)
 *
 *   This simplicity makes the Python side trivial:
 *     lib = ctypes.CDLL("./libdilder.so")
 *     lib.dilder_init()
 *     lib.dilder_tick()
 *     hunger = lib.dilder_get_hunger()
 */

#ifndef DILDER_API_H
#define DILDER_API_H

/*
 * C++ Compatibility Guard
 *
 * If this header is included from a C++ file, the compiler will see
 * `__cplusplus` as defined.  C++ "mangles" function names (adds type
 * information to the name for overloading support), which would make
 * the function names in the shared library different from what ctypes
 * expects.
 *
 * `extern "C" { ... }` tells the C++ compiler: "use plain C naming for
 * everything inside these braces."  This ensures the function names in
 * the compiled library match exactly what's written here (e.g.,
 * "dilder_init" stays as "dilder_init", not "_Z11dilder_initv").
 *
 * The matching closing brace is at the bottom of the file.
 * C compilers ignore this entirely because __cplusplus is not defined.
 */
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>    /* uint8_t for the framebuffer pointer */
#include <stdbool.h>   /* bool (not used in the API, but included for completeness) */

/*
 * Screen dimensions -- duplicated here (also in game_state.h) so that
 * code including only dilder.h can know the display size without pulling
 * in the full game state header.
 */
#define DILDER_SCREEN_W 250
#define DILDER_SCREEN_H 122

/* ================================================================
 *  Lifecycle Functions
 *
 *  These control the game's overall lifecycle: start, advance, and
 *  reset.  The DevTool calls these to drive the simulation.
 * ================================================================ */

/* Initialize all game systems and start a new game.
 * Must be called once before any other dilder_* function. */
void dilder_init(void);

/*
 * Advance one game tick.
 * Each call simulates one game-second: stat decay, emotion evaluation,
 * sensor processing, UI rendering, etc. all happen inside this call.
 * Call at ~1 Hz for real-time play, or faster for fast-forward/debug.
 */
void dilder_tick(void);

/* Reset to a fresh new game (equivalent to init, but semantically a "restart"). */
void dilder_reset(void);

/* ================================================================
 *  Input
 *
 *  Simulate button presses.  Parameters are plain ints (not enums)
 *  for FFI compatibility.
 * ================================================================ */

/*
 * Simulate a button press.
 *   button_id:  1=up, 2=down, 3=select, 4=back, 5=action  (0=none, ignored)
 *   press_type: 1=short, 2=long, 3=double  (0=none, ignored)
 */
void dilder_button_press(int button_id, int press_type);

/* ================================================================
 *  Sensor Emulation
 *
 *  On the desktop build, there are no physical sensors.  These functions
 *  let the DevTool feed fake sensor values into the game engine so it
 *  behaves as if real sensors were present.
 *
 *  Boolean parameters use `int` (0 or 1) instead of `bool` because
 *  ctypes handles int more reliably across platforms.
 * ================================================================ */

void dilder_set_light(float lux);            /* ambient light in lux */
void dilder_set_temperature(float celsius);  /* temperature in Celsius */
void dilder_set_humidity(float percent);     /* relative humidity 0-100 */
void dilder_set_mic_level(int level);        /* microphone sound level */
void dilder_set_steps(int step_count);       /* total step count */
void dilder_set_shaking(int shaking);        /* 1 = shaking, 0 = not */
void dilder_set_walking(int walking);        /* 1 = walking, 0 = not */
void dilder_set_at_home(int at_home);        /* 1 = at home, 0 = away */

/* ================================================================
 *  Display Output
 * ================================================================ */

/*
 * Returns a pointer to the 250x122 1bpp framebuffer (3904 bytes).
 *
 * Memory layout:
 *   - Row-major: byte 0 is the start of row 0, byte 32 is the start of row 1.
 *   - MSB-first per byte: bit 7 of each byte is the leftmost pixel.
 *   - 1 = black pixel, 0 = white pixel.
 *   - 32 bytes per row (250 pixels / 8 = 31.25, rounded up to 32).
 *
 * The returned pointer is "const" -- the caller may read the bytes but
 * must not modify them.  The pointer points to a global array that
 * persists for the lifetime of the program (no need to free it).
 */
const uint8_t *dilder_get_framebuffer(void);

/* ================================================================
 *  Game State Queries
 *
 *  These functions read internal game state and return it as simple
 *  types.  Enum values are returned as int so Python doesn't need to
 *  know about the C enum definitions.
 * ================================================================ */

int         dilder_get_game_state(void);   /* returns game_state_t as int */
int         dilder_get_emotion(void);      /* returns emotion_id_t as int */
int         dilder_get_life_stage(void);   /* returns life_stage_t as int */
int         dilder_get_tick_count(void);   /* total ticks since game start */

/* Primary stats (each is 0-100 range) */
int         dilder_get_hunger(void);
int         dilder_get_happiness(void);
int         dilder_get_energy(void);
int         dilder_get_hygiene(void);
int         dilder_get_health(void);
int         dilder_get_weight(void);

/* Secondary / progression stats */
int         dilder_get_bond_xp(void);      /* total bond experience points */
int         dilder_get_bond_level(void);   /* returns bond_level_t as int */
int         dilder_get_discipline(void);   /* discipline score */
int         dilder_get_age_seconds(void);  /* pet age in game-seconds */

/* Sensor readback -- returns the values the game engine is currently using */
float       dilder_get_sensor_light(void);     /* light in lux */
float       dilder_get_sensor_temp(void);      /* temperature in Celsius */
float       dilder_get_sensor_humidity(void);  /* humidity percentage */

/*
 * String queries -- return pointers to static, read-only C strings.
 *
 * "const char *" means: pointer to a string you may read but must not
 * modify or free.  The strings live in the program's read-only data
 * segment and are valid for the entire lifetime of the process.
 *
 * In Python (via ctypes), these come back as bytes that you decode to
 * a Python string:  result = lib.dilder_get_emotion_name().decode("utf-8")
 */
const char *dilder_get_emotion_name(void);    /* e.g., "hungry", "excited" */
const char *dilder_get_stage_name(void);      /* e.g., "egg", "adult" */
const char *dilder_get_state_name(void);      /* e.g., "active", "sleeping" */
const char *dilder_get_dialogue_text(void);   /* current dialogue, or "" if none */

/*
 * Closing brace for the `extern "C"` block opened above.
 * Only compiled when a C++ compiler is used.
 */
#ifdef __cplusplus
}
#endif

#endif /* DILDER_API_H */
