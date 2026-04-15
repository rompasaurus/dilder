/*
 * sensor.c -- Sensor Emulation Layer
 *
 * PURPOSE:
 *   On real hardware (the Dilder PCB), this module would talk to physical
 *   sensors over I2C -- the AHT20 for temperature/humidity, the BH1750 for
 *   ambient light, an accelerometer, a microphone ADC, etc.
 *
 *   Because we're running on a desktop emulator, none of those chips exist.
 *   Instead, this file provides "emulated" sensor data: the DevTool GUI calls
 *   the sensor_emu_set_*() functions to push fake values in, and the game
 *   loop calls sensor_poll() to read them back out.
 *
 *   This is a common embedded pattern called a "Hardware Abstraction Layer"
 *   (HAL). The rest of the game code never knows whether it's talking to real
 *   hardware or an emulation -- it just calls sensor_poll() and gets a
 *   sensor_context_t back.
 *
 * MEMORY MODEL:
 *   The two main variables (emu_ctx, prev_ctx) are declared `static` at file
 *   scope. In C, `static` at file scope means:
 *     1. They live for the entire lifetime of the program (not on the stack).
 *     2. They are only visible inside THIS file -- other .c files cannot
 *        access them directly. This gives us encapsulation (like "private"
 *        in other languages).
 *   Both structs are stored in the BSS segment (zero-initialized global
 *   memory) since they're static, though sensor_init() explicitly zeroes
 *   them with memset for clarity.
 */

#include "sensor/sensor.h"
#include "game/event.h"
#include "game/time_mgr.h"

/* ─── Emulated Sensor State ──────────────────────────────────── */

/*
 * emu_ctx holds the CURRENT emulated sensor readings. When the DevTool
 * adjusts a slider (e.g., light level), it calls sensor_emu_set_light()
 * which updates this struct.
 *
 * prev_ctx holds the PREVIOUS frame's readings, so we can detect
 * transitions (e.g., "light just jumped by 300 lux" or "mic zone
 * changed from quiet to yelling").
 *
 * Both are `static` -- private to this file, invisible to other modules.
 * This is the C equivalent of private member variables in a class.
 */
static sensor_context_t emu_ctx;
static sensor_context_t prev_ctx;

/*
 * sensor_init -- Reset all emulated sensor data to comfortable defaults.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Called once at startup. Uses memset() to zero out every byte of both
 * structs, then sets "comfortable indoor" defaults so the pet starts
 * happy. memset(&emu_ctx, 0, sizeof(emu_ctx)) means: starting at the
 * memory address of emu_ctx, write 0x00 into every byte for
 * sizeof(emu_ctx) bytes. This is a fast way to zero a struct in C.
 */
void sensor_init(void) {
    memset(&emu_ctx, 0, sizeof(emu_ctx));
    memset(&prev_ctx, 0, sizeof(prev_ctx));

    /* Default comfortable environment */
    emu_ctx.light.lux = 300.0f;        /* 300 lux = typical indoor lighting  */
    emu_ctx.light.zone = LIGHT_INDOOR; /* Categorical zone for game logic    */
    emu_ctx.env.celsius = 22.0f;       /* Room temperature (22 C / ~72 F)    */
    emu_ctx.env.humidity_pct = 50.0f;  /* 50% humidity -- comfortable range  */
    emu_ctx.env.comfort_zone = COMFORT_GOOD;
    emu_ctx.mic.level = 0;             /* Silence                            */
    emu_ctx.mic.zone = MIC_SILENT;
    emu_ctx.wifi.at_home = true;       /* Pet starts "at home"               */
}

/* ─── Emulation Setters ──────────────────────────────────────── */
/*
 * Each setter below is called by the DevTool GUI when the user moves
 * a slider or toggles a checkbox. They update the emulated sensor
 * context and also compute derived values (like which "zone" a raw
 * reading falls into). On real hardware, the zone classification
 * would happen inside sensor_poll() after reading the actual I2C
 * registers.
 */

/*
 * sensor_emu_set_light -- Set the emulated ambient light level.
 *
 * Parameters:
 *   lux  -- light intensity in lux (0 = pitch dark, 500+ = bright)
 *
 * Returns: nothing
 *
 * Also computes delta_lux (the change from previous reading), which
 * is used by sensor_classify_events() to detect sudden light changes
 * that might mean the pet was picked up or uncovered.
 *
 * The chained if/else-if is a "threshold classifier" -- it maps a
 * continuous value (lux) into discrete categories (zones) that the
 * game logic is easier to write against.
 */
void sensor_emu_set_light(float lux) {
    emu_ctx.light.delta_lux = lux - emu_ctx.light.lux;  /* change since last set */
    emu_ctx.light.lux = lux;

    /* Classify the raw lux value into a discrete zone.
     * The order matters: check from brightest to darkest. */
    if (lux > 500.0f)      emu_ctx.light.zone = LIGHT_BRIGHT;
    else if (lux > 100.0f) emu_ctx.light.zone = LIGHT_INDOOR;
    else if (lux > 10.0f)  emu_ctx.light.zone = LIGHT_DIM;
    else                     emu_ctx.light.zone = LIGHT_DARK;
}

/*
 * sensor_emu_set_temperature -- Set the emulated temperature in Celsius.
 *
 * Parameters:
 *   celsius  -- temperature value (e.g. 22.0 for room temp)
 *
 * Returns: nothing
 *
 * Also recalculates the comfort_zone, which depends on BOTH temperature
 * AND humidity. The comfort zone drives emotion changes -- if it's too
 * hot or cold, the pet gets unhappy.
 */
void sensor_emu_set_temperature(float celsius) {
    emu_ctx.env.celsius = celsius;

    /* Recalculate comfort zone.
     * "Good" requires BOTH temperature 18-24 C AND humidity 40-60%.
     * Otherwise, classify by the temperature extreme. */
    if (celsius >= 18.0f && celsius <= 24.0f &&
        emu_ctx.env.humidity_pct >= 40.0f && emu_ctx.env.humidity_pct <= 60.0f) {
        emu_ctx.env.comfort_zone = COMFORT_GOOD;
    } else if (celsius > 28.0f) {
        emu_ctx.env.comfort_zone = COMFORT_HOT;
    } else if (celsius < 15.0f) {
        emu_ctx.env.comfort_zone = COMFORT_COLD;
    } else {
        emu_ctx.env.comfort_zone = COMFORT_GOOD;
    }
}

/*
 * sensor_emu_set_humidity -- Set the emulated relative humidity.
 *
 * Parameters:
 *   percent  -- humidity as a percentage (0.0 to 100.0)
 *
 * Returns: nothing
 *
 * Like set_temperature, this also recalculates the comfort zone because
 * comfort depends on the combination of temp + humidity.
 */
void sensor_emu_set_humidity(float percent) {
    emu_ctx.env.humidity_pct = percent;

    /* Recalculate comfort zone based on both temp and humidity */
    if (emu_ctx.env.celsius >= 18.0f && emu_ctx.env.celsius <= 24.0f &&
        percent >= 40.0f && percent <= 60.0f) {
        emu_ctx.env.comfort_zone = COMFORT_GOOD;
    } else if (percent > 70.0f) {
        emu_ctx.env.comfort_zone = COMFORT_HUMID;
    } else if (percent < 30.0f) {
        emu_ctx.env.comfort_zone = COMFORT_DRY;
    }
}

/*
 * sensor_emu_set_mic_level -- Set the emulated microphone amplitude.
 *
 * Parameters:
 *   level  -- raw ADC-style level (0 = silent, 2000+ = yelling)
 *             uint16_t means unsigned 16-bit integer (0 to 65535)
 *
 * Returns: nothing
 *
 * Maps the raw level into zones that game logic uses. On real hardware,
 * this would come from sampling the microphone's analog-to-digital
 * converter and computing a running average / peak.
 */
void sensor_emu_set_mic_level(uint16_t level) {
    emu_ctx.mic.level = level;
    emu_ctx.mic.peak = level;   /* In emulation, peak = current level */

    /* Threshold classification, similar to the light zone logic */
    if (level < 50)       emu_ctx.mic.zone = MIC_SILENT;
    else if (level < 200) emu_ctx.mic.zone = MIC_QUIET;
    else if (level < 800) emu_ctx.mic.zone = MIC_MODERATE;
    else if (level < 2000)emu_ctx.mic.zone = MIC_LOUD;
    else                   emu_ctx.mic.zone = MIC_YELL;
}

/*
 * sensor_emu_set_steps -- Set the emulated step counter.
 *
 * Parameters:
 *   step_count  -- total cumulative steps (uint32_t = unsigned 32-bit,
 *                  so up to ~4.3 billion steps)
 *
 * Returns: nothing
 *
 * Also calculates steps_since_last -- how many new steps happened since
 * the previous call. The ternary operator (condition ? a : b) guards
 * against the counter going backwards (which shouldn't happen, but
 * defensive programming prevents underflow in unsigned subtraction).
 */
void sensor_emu_set_steps(uint32_t step_count) {
    uint32_t prev = emu_ctx.accel.step_count;   /* remember old count */
    emu_ctx.accel.step_count = step_count;

    /* Calculate delta. The ternary prevents unsigned underflow:
     * if step_count somehow went backwards, we report 0 new steps
     * instead of a huge garbage number (because uint32_t can't be negative). */
    emu_ctx.accel.steps_since_last = (step_count > prev) ? step_count - prev : 0;
}

/*
 * sensor_emu_set_accel -- Set raw accelerometer X/Y/Z readings.
 *
 * Parameters:
 *   x, y, z  -- acceleration on each axis (int16_t = signed 16-bit,
 *               range -32768 to +32767). On real hardware these come
 *               from an accelerometer like the LIS3DH.
 *
 * Returns: nothing
 */
void sensor_emu_set_accel(int16_t x, int16_t y, int16_t z) {
    emu_ctx.accel.x = x;
    emu_ctx.accel.y = y;
    emu_ctx.accel.z = z;
}

/*
 * sensor_emu_set_shaking -- Set whether the device is being shaken.
 *
 * Parameters:
 *   shaking  -- true if shaking, false if not (bool from <stdbool.h>)
 *
 * Returns: nothing
 *
 * On real hardware, shaking would be detected by analyzing rapid
 * oscillations in the accelerometer data.
 */
void sensor_emu_set_shaking(bool shaking) {
    emu_ctx.accel.shaking = shaking;
}

/*
 * sensor_emu_set_walking -- Set whether the user is walking.
 *
 * Parameters:
 *   walking  -- true if walking, false if stopped
 *
 * Returns: nothing
 *
 * Mutually exclusive with running -- setting walking clears running.
 * On real hardware, a pedometer algorithm would classify the motion
 * pattern.
 */
void sensor_emu_set_walking(bool walking) {
    emu_ctx.accel.walking = walking;
    emu_ctx.accel.running = false;  /* walking and running are mutually exclusive */
}

/*
 * sensor_emu_set_at_home -- Set whether the device is at home (via WiFi).
 *
 * Parameters:
 *   at_home  -- true if connected to home WiFi, false if away
 *
 * Returns: nothing
 *
 * On real hardware, this would check if a known home WiFi SSID is
 * in range. The away_duration_ms counter tracks how long the pet has
 * been away, which affects emotions (homesickness, etc.).
 */
void sensor_emu_set_at_home(bool at_home) {
    emu_ctx.wifi.at_home = at_home;
    emu_ctx.wifi.away_from_home = !at_home;   /* logical inverse */
    if (!at_home) {
        emu_ctx.wifi.away_duration_ms += 1000; /* accumulate away time */
    } else {
        emu_ctx.wifi.away_duration_ms = 0;     /* reset when home */
    }
}

/* ─── Polling ────────────────────────────────────────────────── */

/*
 * sensor_poll -- Return the current snapshot of all sensor data.
 *
 * Parameters:
 *   now_ms  -- current time in milliseconds (used to timestamp the reading)
 *
 * Returns:
 *   A COPY of the sensor_context_t struct (returned by value, not by
 *   pointer). In C, returning a struct by value means the entire struct
 *   gets copied onto the caller's stack. This is safe because
 *   sensor_context_t is not huge (~80 bytes), and it gives the caller
 *   an immutable snapshot that won't change if the DevTool updates
 *   values between frames.
 *
 * On real hardware, this function would read all I2C/SPI/ADC sensors
 * and pack the results into the struct. In emulation, the values are
 * already set by the sensor_emu_set_*() functions, so we just stamp
 * the time and return.
 */
sensor_context_t sensor_poll(uint32_t now_ms) {
    emu_ctx.timestamp = now_ms;
    return emu_ctx;   /* returns a copy of the entire struct */
}

/* ─── Event Classification ───────────────────────────────────── */

/*
 * sensor_classify_events -- Compare previous and current sensor readings
 *                           to detect meaningful changes and fire game events.
 *
 * Parameters:
 *   prev  -- pointer to the PREVIOUS frame's sensor snapshot
 *   curr  -- pointer to the CURRENT frame's sensor snapshot
 *            Both are `const` pointers, meaning this function promises
 *            not to modify the data they point to. This is good practice
 *            for "read-only" parameters.
 *
 * Returns: nothing (fires events as side effects via event_fire())
 *
 * This is the bridge between raw sensor data and the game's event system.
 * By comparing prev vs curr, we detect TRANSITIONS (things that just
 * changed) rather than steady states. For example, we only fire
 * EVENT_LOUD_NOISE when the mic zone BECOMES MIC_YELL, not every frame
 * that it stays at yell level.
 *
 * The -> operator is used to access struct fields through a pointer.
 * curr->light.delta_lux means: "follow the curr pointer to the struct,
 * then access its .light member, then access its .delta_lux field."
 */
void sensor_classify_events(const sensor_context_t *prev,
                            const sensor_context_t *curr) {
    /* Light startle: a sudden increase of 300+ lux might mean the pet
     * was uncovered or picked up into bright light. */
    if (curr->light.delta_lux > 300.0f) {
        event_fire(EVENT_PICKED_UP, NULL);
    }

    /* Mic events: detect transitions into loud/talking states.
     * The && checks that the PREVIOUS state was quieter, so we only
     * fire the event once on the transition, not every frame. */
    if (curr->mic.zone == MIC_YELL && prev->mic.zone < MIC_YELL) {
        event_fire(EVENT_LOUD_NOISE, NULL);
    }
    if (curr->mic.zone == MIC_MODERATE && curr->mic.duration_ms > 3000) {
        event_fire(EVENT_TALKING, NULL);   /* sustained moderate noise = talking */
    }

    /* Motion events: shaking, falling, being picked up.
     * Each checks curr && !prev to detect the START of the action. */
    if (curr->accel.shaking && !prev->accel.shaking) {
        event_fire(EVENT_SHAKEN, NULL);
    }
    if (curr->accel.falling) {
        event_fire(EVENT_DROPPED, NULL);   /* falling = dropped, fire immediately */
    }
    if (curr->accel.picked_up && !prev->accel.picked_up) {
        event_fire(EVENT_PICKED_UP, NULL);
    }

    /* Temperature extreme: fire when comfort transitions FROM good to bad.
     * prev->env.comfort_zone == COMFORT_GOOD ensures we only fire once
     * when the environment first becomes uncomfortable. */
    if ((curr->env.celsius > 28.0f || curr->env.celsius < 15.0f) &&
        prev->env.comfort_zone == COMFORT_GOOD) {
        event_fire(EVENT_TEMPERATURE_EXTREME, NULL);
    }

    /* Home detection: fire events on arrival/departure transitions.
     * curr->wifi.at_home && !prev->wifi.at_home means "now home, wasn't before." */
    if (curr->wifi.at_home && !prev->wifi.at_home) {
        event_fire(EVENT_HOME_ARRIVED, NULL);
    }
    if (!curr->wifi.at_home && prev->wifi.at_home) {
        event_fire(EVENT_HOME_LEFT, NULL);
    }
}
