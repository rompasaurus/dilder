/*
 * time_mgr.c -- Virtual game clock manager
 *
 * This module converts real-world elapsed milliseconds into a virtual
 * wall clock (hours, minutes, seconds, day number) for the game world.
 * The virtual clock starts at 12:00:00 (noon) on day 0 and advances
 * in lockstep with real time (1 real second = 1 game second).
 *
 * Other modules call time_mgr_now_ms() to get the raw millisecond
 * timestamp, or time_mgr_get() to get the structured game time with
 * hour/minute/second/day broken out.
 *
 * Memory model:
 *   Two file-scope static variables hold all state -- no heap allocation.
 *   `platform_ms` is a uint32_t storing the raw millisecond count.
 *   `current_time` is a game_time_t struct with the derived clock fields.
 *   Both live in the BSS segment (static storage duration, zero-initialized
 *   at program start, then set explicitly in time_mgr_init).
 *
 * Key C concepts:
 *   - Integer division and modulo to decompose seconds into h:m:s
 *   - Static variables for persistent module-private state
 *   - Returning a struct by value (copies the struct onto the caller's stack)
 */

#include "game/time_mgr.h"

/* ─── State ──────────────────────────────────────────────────── */

/*
 * platform_ms -- Raw millisecond counter from the hardware timer or emulator.
 *
 * This is the single source of truth for "what time is it?" in the firmware.
 * On real hardware, it comes from a hardware timer. In the emulator, it's
 * injected via time_mgr_set_ms() or time_mgr_advance().
 *
 * "static" at file scope = private to this file (internal linkage).
 */
static uint32_t   platform_ms = 0;

/*
 * current_time -- The derived game clock (hour, minute, second, day, etc.).
 *
 * This struct is recalculated every tick by time_mgr_update(). Other modules
 * can read it via time_mgr_get(), which returns a copy (not a pointer).
 * Returning a copy means the caller gets a snapshot that won't change
 * unexpectedly -- a safe pattern for embedded systems.
 */
static game_time_t current_time;

/*
 * time_mgr_init -- Reset the time manager to its initial state.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Zeroes out the platform clock and the game time struct, then sets
 * the starting hour to 12 (noon) and marks it as daytime.
 *
 * memset(&current_time, 0, sizeof(current_time))
 *   - `&current_time` takes the address of the struct (pointer to it).
 *   - `sizeof(current_time)` gives the size in bytes of the struct.
 *   - This zeroes ALL fields: now_ms=0, hour=0, minute=0, etc.
 *   - Then we overwrite hour and is_daytime with our desired start values.
 */
void time_mgr_init(void) {
    platform_ms = 0;
    memset(&current_time, 0, sizeof(current_time));  /* zero every field */
    current_time.hour = 12;  /* start at noon */
    current_time.is_daytime = true;
}

/*
 * time_mgr_update -- Recalculate the game clock from raw milliseconds.
 *
 * Parameters:
 *   real_ms -- The current platform time in milliseconds.
 *
 * Returns:
 *   A game_time_t struct with hour/minute/second/day computed.
 *   Returned BY VALUE, meaning the caller gets a full copy on their stack.
 *
 * The clock starts at 12:00:00 and wraps every 24 hours (86400 seconds).
 *
 * Arithmetic breakdown:
 *   total_seconds = real_ms / 1000
 *       Integer division: 1500ms / 1000 = 1 (truncates, no rounding).
 *
 *   day_seconds = total_seconds % 86400
 *       Modulo wraps the second count within a single day (0..86399).
 *       86400 = 24 hours * 60 minutes * 60 seconds.
 *
 *   hour = (12 + day_seconds / 3600) % 24
 *       day_seconds / 3600 gives hours elapsed since midnight.
 *       We add 12 because the game starts at noon, then wrap with % 24.
 *
 *   minute = (day_seconds % 3600) / 60
 *       day_seconds % 3600 gives seconds within the current hour.
 *       Dividing by 60 converts to minutes.
 *
 *   second = day_seconds % 60
 *       Remainder after removing full minutes = seconds within the minute.
 *
 *   day = total_seconds / 86400
 *       Total number of full days elapsed.
 *
 *   is_daytime = hour in [6, 22)
 *       Daytime is 6:00 AM to 9:59 PM.
 */
game_time_t time_mgr_update(uint32_t real_ms) {
    platform_ms = real_ms;
    current_time.now_ms = real_ms;

    /* Derive wall clock from elapsed seconds.
     * In emulation, 1 game-second = 1 real tick.
     * We track a virtual clock starting at 12:00:00 day 0. */
    uint32_t total_seconds = real_ms / 1000;       /* ms -> whole seconds */
    uint32_t day_seconds = total_seconds % 86400;  /* seconds within today */

    current_time.hour   = (12 + day_seconds / 3600) % 24;  /* noon-based hour */
    current_time.minute = (day_seconds % 3600) / 60;       /* minutes in hour */
    current_time.second = day_seconds % 60;                 /* seconds in minute */
    current_time.day    = total_seconds / 86400;            /* full days elapsed */
    current_time.is_daytime = (current_time.hour >= 6 && current_time.hour < 22);

    return current_time;  /* return by value: caller gets a stack copy */
}

/*
 * time_mgr_get -- Return the most recently computed game time.
 *
 * Parameters: none
 * Returns:    A copy of current_time (the game_time_t struct).
 *
 * Unlike time_mgr_update(), this does NOT recalculate -- it just returns
 * whatever was last computed. Useful when you need the time but don't
 * want to advance the clock.
 */
game_time_t time_mgr_get(void) {
    return current_time;  /* returns a copy, not a reference */
}

/*
 * time_mgr_now_ms -- Return the raw platform millisecond counter.
 *
 * Parameters: none
 * Returns:    The current value of platform_ms.
 *
 * This is the most-called function in the codebase. Every module that
 * needs a timestamp (event system, stat timers, cooldowns) calls this
 * rather than accessing a hardware register directly. This abstraction
 * makes it easy to swap between real hardware and emulation.
 */
uint32_t time_mgr_now_ms(void) {
    return platform_ms;
}

/*
 * time_mgr_set_ms -- Directly set the platform clock (for emulation/testing).
 *
 * Parameters:
 *   ms -- The new millisecond value to set.
 *
 * Returns: nothing
 *
 * Sets the raw millisecond counter and then recalculates the derived
 * game clock. Used by the emulator to inject synthetic time.
 */
void time_mgr_set_ms(uint32_t ms) {
    platform_ms = ms;
    time_mgr_update(ms);  /* recalculate hour/min/sec/day from new time */
}

/*
 * time_mgr_advance -- Jump forward by a given number of milliseconds.
 *
 * Parameters:
 *   delta_ms -- How many milliseconds to advance.
 *
 * Returns: nothing
 *
 * Adds delta_ms to the current platform time, then recalculates.
 * Useful for fast-forward in the emulator (e.g. "skip ahead 1 hour").
 */
void time_mgr_advance(uint32_t delta_ms) {
    platform_ms += delta_ms;       /* advance the raw counter */
    time_mgr_update(platform_ms);  /* derive the new game clock */
}
