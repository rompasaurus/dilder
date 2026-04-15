/*
 * Dilder Shared Library API  (dilder_api.c)
 *
 * PURPOSE:
 *   This file is the "bridge" between Python (the DevTool GUI) and C (the
 *   game engine).  It implements every function declared in dilder.h.
 *
 * HOW IT WORKS:
 *   The DevTool is written in Python.  Python cannot call C code directly,
 *   so it uses a mechanism called "ctypes" -- the C Foreign Function
 *   Interface (FFI).  ctypes loads the compiled .so/.dll shared library at
 *   runtime and can call any function exported from it.
 *
 *   For this to work, every function in the public API must:
 *     1. Use C linkage (not C++ -- see the extern "C" guard in dilder.h).
 *     2. Use simple types that ctypes understands: int, float,
 *        const char *, const uint8_t *, etc.  No structs passed by value,
 *        no C++ objects, no templates.
 *
 *   This file is essentially a thin wrapper: each function here converts
 *   between the simple FFI-friendly types and the internal game engine
 *   types (enums, structs, etc.) that live in game_state.h.
 */

#include "dilder.h"
#include "game/game_loop.h"
#include "game/game_state.h"
#include "game/stat.h"
#include "game/emotion.h"
#include "game/time_mgr.h"
#include "sensor/sensor.h"
#include "ui/ui.h"
#include "ui/input.h"
#include "ui/render.h"

/*
 * Emulated time in milliseconds.
 *
 * "static" means this variable is only visible inside this .c file --
 * no other file can access it directly.  This is C's way of doing
 * file-private / module-level encapsulation.
 *
 * On real hardware, time comes from a hardware timer.  In the desktop
 * build we manually advance this counter so the game thinks time is
 * passing.
 */
static uint32_t emu_time_ms = 0;

/* ================================================================
 *  Lifecycle Functions
 *  Called by Python to create, advance, and reset the game.
 * ================================================================ */

/*
 * dilder_init -- start a brand-new game.
 *
 * Resets the emulated clock to zero and calls game_loop_init(), which
 * zeroes out the global game struct (g_game) and puts everything in its
 * default state (egg stage, full stats, etc.).
 */
void dilder_init(void) {
    emu_time_ms = 0;
    game_loop_init();
}

/*
 * dilder_tick -- advance the game by one tick (one game-second).
 *
 * Each call adds 1000 ms to the emulated clock and runs one full
 * iteration of the game loop: stat decay, emotion evaluation, UI
 * rendering, etc.
 *
 * The DevTool calls this once per real second for normal play, or
 * many times per second when "fast-forwarding" for testing.
 */
void dilder_tick(void) {
    emu_time_ms += 1000;  /* each tick = 1 game second */
    game_loop_tick(emu_time_ms);
}

/*
 * dilder_reset -- restart the game from scratch.
 *
 * Identical to init: resets the clock and reinitializes game state.
 * Provided as a separate function so the DevTool can expose a clear
 * "Reset" button without worrying about internal details.
 */
void dilder_reset(void) {
    emu_time_ms = 0;
    game_loop_init();
}

/* ================================================================
 *  Input
 *  Lets Python send button presses into the game engine.
 * ================================================================ */

/*
 * dilder_button_press -- simulate a physical button press.
 *
 * Parameters use plain `int` instead of the C enums (button_id_t,
 * press_type_t) because Python ctypes can only send simple integers.
 * Inside the function we cast them to the proper enum types.
 *
 * The range checks prevent invalid values from reaching the input
 * system.  button_id 1-5 maps to BTN_UP..BTN_ACTION; press_type 1-3
 * maps to PRESS_SHORT..PRESS_DOUBLE.  Anything outside those ranges
 * is silently ignored (the `return` exits the function early).
 */
void dilder_button_press(int button_id, int press_type) {
    if (button_id <= 0 || button_id > 5) return;   /* guard: invalid button */
    if (press_type <= 0 || press_type > 3) return;  /* guard: invalid press  */

    /*
     * (button_id_t)button_id  is a C "cast" -- it tells the compiler
     * "treat this int as a button_id_t enum value."  The underlying
     * bits don't change, but the compiler now knows the intended type.
     */
    input_push((button_id_t)button_id, (press_type_t)press_type);
}

/* ================================================================
 *  Sensor Emulation
 *
 *  On real hardware, sensors (light, temperature, accelerometer, etc.)
 *  produce readings automatically.  On the desktop build we don't have
 *  physical sensors, so Python feeds fake values through these functions.
 *
 *  Each function takes a simple FFI-friendly type (float or int) and
 *  forwards it to the sensor emulation layer, casting where needed.
 * ================================================================ */

void dilder_set_light(float lux) {
    sensor_emu_set_light(lux);
}

void dilder_set_temperature(float celsius) {
    sensor_emu_set_temperature(celsius);
}

void dilder_set_humidity(float percent) {
    sensor_emu_set_humidity(percent);
}

/*
 * Microphone level arrives as `int` from Python.  The engine stores it
 * as uint16_t (unsigned 16-bit), so we cast it.  (uint16_t) is 0..65535.
 */
void dilder_set_mic_level(int level) {
    sensor_emu_set_mic_level((uint16_t)level);
}

/*
 * Step count arrives as `int` from Python.  The engine stores it as
 * uint32_t (unsigned 32-bit, 0..~4 billion) because step counts are
 * always positive and can grow large over time.
 */
void dilder_set_steps(int step_count) {
    sensor_emu_set_steps((uint32_t)step_count);
}

/*
 * Boolean values come from Python as int (0 or 1) because ctypes has
 * no native bool.  The expression `shaking != 0` converts any non-zero
 * int to the C `true` value (1), and zero to `false` (0).
 */
void dilder_set_shaking(int shaking) {
    sensor_emu_set_shaking(shaking != 0);
}

void dilder_set_walking(int walking) {
    sensor_emu_set_walking(walking != 0);
}

void dilder_set_at_home(int at_home) {
    sensor_emu_set_at_home(at_home != 0);
}

/* ================================================================
 *  Display Output
 *  Lets Python read the rendered screen.
 * ================================================================ */

/*
 * dilder_get_framebuffer -- return a pointer to the display memory.
 *
 * `const uint8_t *` means "pointer to read-only bytes."
 *   - `uint8_t` = unsigned 8-bit integer (one byte, 0..255).
 *   - `const` = Python may read but must not write through this pointer.
 *   - `*` = this is a pointer (a memory address), not a copy of the data.
 *
 * g_framebuffer is a global array of 3904 bytes that holds the 250x122
 * 1-bit-per-pixel display image.  Rather than copying 3904 bytes every
 * frame, we just hand Python the address of the existing array so it
 * can read the pixels directly.  This is efficient: zero copies.
 *
 * Python (via ctypes) will dereference this pointer to read the bytes
 * and convert them into a displayable image.
 */
const uint8_t *dilder_get_framebuffer(void) {
    return g_framebuffer;
}

/* ================================================================
 *  Game State Queries
 *
 *  Each function reads a field from the global game struct (g_game) and
 *  returns it as a plain `int` or `float` that Python can understand.
 *
 *  The `(int)` casts convert C enums and fixed-width integers (int16_t,
 *  uint32_t, etc.) to a standard `int`.  This is necessary because
 *  Python ctypes expects a consistent return type.
 * ================================================================ */

/* Returns the current game state as an int (see game_state_t enum) */
int dilder_get_game_state(void) {
    return (int)g_game.state;
}

/* Returns the current emotion as an int (see emotion_id_t enum) */
int dilder_get_emotion(void) {
    return (int)g_game.emotion.current;
}

/* Returns the current life stage as an int (see life_stage_t enum) */
int dilder_get_life_stage(void) {
    return (int)g_game.life.stage;
}

/* Returns how many ticks have passed since game start */
int dilder_get_tick_count(void) {
    return (int)g_game.tick_count;
}

/* --- Primary stats (each is 0-100 range, stored as int16_t) --- */

int dilder_get_hunger(void) {
    return (int)g_game.stats.primary.hunger;
}

int dilder_get_happiness(void) {
    return (int)g_game.stats.primary.happiness;
}

int dilder_get_energy(void) {
    return (int)g_game.stats.primary.energy;
}

int dilder_get_hygiene(void) {
    return (int)g_game.stats.primary.hygiene;
}

int dilder_get_health(void) {
    return (int)g_game.stats.primary.health;
}

/* Weight is a secondary stat (can go above 100) */
int dilder_get_weight(void) {
    return (int)g_game.stats.secondary.weight;
}

/* --- Progression --- */

int dilder_get_bond_xp(void) {
    return (int)g_game.progression.bond_xp;
}

int dilder_get_bond_level(void) {
    return (int)g_game.progression.bond_level;
}

int dilder_get_discipline(void) {
    return (int)g_game.stats.secondary.discipline;
}

int dilder_get_age_seconds(void) {
    return (int)g_game.life.age_seconds;
}

/* --- Sensor readbacks (what the game currently sees) --- */

float dilder_get_sensor_light(void) {
    return g_game.sensor.light.lux;
}

float dilder_get_sensor_temp(void) {
    return g_game.sensor.env.celsius;
}

float dilder_get_sensor_humidity(void) {
    return g_game.sensor.env.humidity_pct;
}

/* ================================================================
 *  String Queries
 *
 *  These return `const char *` -- a pointer to a C string.  The strings
 *  are "static" (they live in read-only program memory and never get
 *  freed), so Python can safely read them at any time.  The "const"
 *  tells the caller: do not modify or free this string.
 * ================================================================ */

/* Returns the human-readable name of the current emotion (e.g. "hungry") */
const char *dilder_get_emotion_name(void) {
    return emotion_name(g_game.emotion.current);
}

/* Returns the life stage name (e.g. "egg", "hatchling", "adult") */
const char *dilder_get_stage_name(void) {
    return life_stage_name(g_game.life.stage);
}

/* Returns the game state name (e.g. "active", "sleeping", "dead") */
const char *dilder_get_state_name(void) {
    return game_state_name(g_game.state);
}

/*
 * Returns the current dialogue text, or an empty string "" if no
 * dialogue is showing.  The empty string literal "" lives in static
 * memory, so it's always safe to return -- it won't be freed.
 */
const char *dilder_get_dialogue_text(void) {
    if (g_game.dialogue.showing) {
        return g_game.dialogue.current_text;
    }
    return "";
}
