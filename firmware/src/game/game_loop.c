/*
 * game_loop.c -- Top-level game loop: initialization, tick scheduling, and dispatch
 *
 * This is the "main brain" of the firmware. It ties together all the
 * subsystems (stats, events, emotions, life stages, sensors, UI) and
 * runs them in the correct order each frame.
 *
 * Architecture:
 *   The platform (real hardware or emulator) calls game_loop_tick() at
 *   its frame rate (as fast as possible). Inside, we:
 *     1. Process button input
 *     2. Poll sensors
 *     3. Run the 1-second game tick (if enough time has passed)
 *     4. Render the screen (if anything changed)
 *
 *   The 1-second game tick (game_tick) is where all the gameplay logic
 *   runs: stat decay, threshold checks, life stage advancement, emotion
 *   resolution, modifier recalculation, and dialogue triggers.
 *
 * Memory model:
 *   g_game is THE global game instance -- a single game_t struct that
 *   holds ALL game state (stats, emotions, life stage, UI, sensors, etc.).
 *   It's declared here without an initializer, so it goes into the BSS
 *   segment (zero-initialized by the C runtime before main() runs).
 *   No heap (malloc/free) is used anywhere in the game.
 *
 *   The lookup tables (EMOTION_NAMES, STAGE_NAMES, etc.) are "static const"
 *   arrays of string pointers. The strings themselves are string literals
 *   stored in read-only memory (.rodata). The pointer arrays are also const
 *   and live in .rodata.
 *
 * Key C concepts:
 *   - Global variable with `extern` declaration in the header
 *   - String literal arrays (const char *[])
 *   - Bounds-checked array indexing for safe enum-to-string conversion
 *   - memset to zero an entire struct
 *   - Modulo-based tick rate scheduling (should_tick)
 *   - Struct copies via assignment (sensor_context_t)
 */

#include "game/game_loop.h"
#include "game/event.h"
#include "game/stat.h"
#include "game/emotion.h"
#include "game/life.h"
#include "game/dialog.h"
#include "game/progress.h"
#include "game/time_mgr.h"
#include "sensor/sensor.h"
#include "ui/ui.h"
#include "ui/input.h"
#include "ui/render.h"

/* ─── Global Game Instance ───────────────────────────────────── */
/*
 * g_game -- The single global struct holding ALL game state.
 *
 * Declared as `game_t g_game;` at file scope with no initializer.
 * This means:
 *   - It has static storage duration (lives for the entire program).
 *   - It's placed in the BSS segment (zero-initialized automatically).
 *   - It's accessible from other files via `extern game_t g_game;` in
 *     the header (game_state.h).
 *   - sizeof(game_t) is quite large (it contains stats, modifiers,
 *     emotion state, life state, sensor data, UI state, etc.), but since
 *     it's global/static, it does NOT consume stack space.
 *
 * Why one big global struct?
 *   On embedded systems with limited RAM, having one struct makes memory
 *   usage predictable and avoids heap fragmentation. Every subsystem
 *   accesses its portion via g_game.stats, g_game.emotion, etc.
 */
game_t g_game;

/* ─── Tick Interval ──────────────────────────────────────────── */
/*
 * TICK_INTERVAL_MS -- How often the core game tick runs, in milliseconds.
 * 1000ms = 1 second. The game_loop_tick() function is called every frame
 * (potentially many times per second), but it only calls game_tick()
 * once per TICK_INTERVAL_MS.
 */
#define TICK_INTERVAL_MS 1000

/*
 * prev_sensor_ctx -- Previous frame's sensor readings.
 *
 * Stored so we can compare current vs. previous sensor data to detect
 * changes (e.g. "was the device just picked up?" or "did the light
 * suddenly change?"). sensor_classify_events() does this comparison.
 *
 * "static" at file scope = private to this file.
 * This is a full struct copy, not a pointer -- it holds its own data.
 */
static sensor_context_t prev_sensor_ctx;

/* ─── Name Lookup Tables ─────────────────────────────────────── */
/*
 * These arrays map enum values to human-readable strings.
 *
 * `static const char *ARRAY[]` means:
 *   - static: only visible within this file
 *   - const char *: each element is a pointer to a read-only string
 *   - The string literals ("Normal", "Hungry", etc.) are stored in the
 *     .rodata (read-only data) section of the binary. The array itself
 *     just holds pointers to those strings.
 *
 * The order of strings MUST match the order of the corresponding enum.
 * For example, EMOTION_NAMES[0] = "Normal" matches EMOTION_NORMAL = 0.
 */

static const char *EMOTION_NAMES[] = {
    "Normal", "Hungry", "Tired", "Sad", "Angry",
    "Excited", "Chill", "Lazy", "Fat", "Chaotic",
    "Weird", "Unhinged", "SlapHappy", "Creepy",
    "Nostalgic", "Homesick"
};

static const char *STAGE_NAMES[] = {
    "Egg", "Hatchling", "Juvenile", "Adolescent", "Adult", "Elder"
};

static const char *STATE_NAMES[] = {
    "Boot", "Active", "Menu", "Sleeping", "Hunt", "Event", "Dead"
};

static const char *CARE_NAMES[] = {
    "Feed Meal", "Feed Snack", "Feed Treat", "Clean",
    "Medicine", "Pet", "Play", "Tickle", "Scold", "Sleep Toggle"
};

/*
 * emotion_name -- Convert an emotion enum to its display name string.
 *
 * Parameters:
 *   id -- The emotion_id_t enum value.
 *
 * Returns:
 *   A pointer to a string literal (e.g. "Hungry"), or "???" if the
 *   enum value is out of range.
 *
 * The bounds check `id < EMOTION_COUNT` prevents reading past the end
 * of the array. EMOTION_COUNT is the last value in the enum and equals
 * the number of valid entries.
 *
 * The returned pointer points to a string literal in .rodata -- it's
 * always valid (no lifetime issues) and must not be modified by the caller.
 */
const char *emotion_name(emotion_id_t id) {
    if (id < EMOTION_COUNT) return EMOTION_NAMES[id];
    return "???";  /* fallback for invalid enum values */
}

/*
 * life_stage_name -- Convert a life stage enum to its display name.
 *
 * Parameters:
 *   stage -- The life_stage_t enum value.
 *
 * Returns:
 *   A pointer to a string literal (e.g. "Hatchling"), or "???".
 */
const char *life_stage_name(life_stage_t stage) {
    if (stage < LIFE_STAGE_COUNT) return STAGE_NAMES[stage];
    return "???";
}

/*
 * game_state_name -- Convert a game state enum to its display name.
 *
 * Parameters:
 *   state -- The game_state_t enum value.
 *
 * Returns:
 *   A pointer to a string literal (e.g. "Active"), or "???".
 *
 * Note: uses `<=` instead of `<` because GAME_STATE_DEAD is the last
 * valid value and there's no GAME_STATE_COUNT sentinel in this enum.
 */
const char *game_state_name(game_state_t state) {
    if (state <= GAME_STATE_DEAD) return STATE_NAMES[state];
    return "???";
}

/*
 * care_action_name -- Convert a care action enum to its display name.
 *
 * Parameters:
 *   action -- The care_action_t enum value.
 *
 * Returns:
 *   A pointer to a string literal (e.g. "Feed Meal"), or "???".
 */
const char *care_action_name(care_action_t action) {
    if (action < CARE_COUNT) return CARE_NAMES[action];
    return "???";
}

/* ─── Initialization ─────────────────────────────────────────── */

/*
 * game_new -- Reset all game state and start a fresh game.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * This zeros out the entire g_game struct with memset, then initializes
 * each subsystem to its starting state.
 *
 * memset(&g_game, 0, sizeof(game_t)):
 *   - &g_game: address of the global game struct
 *   - 0: the byte value to fill with (zero)
 *   - sizeof(game_t): total size of the struct in bytes
 *   This sets EVERY field to zero (ints=0, floats=0.0, bools=false,
 *   pointers=NULL, enums=first value). Then each subsystem's init
 *   function sets its specific starting values.
 *
 * The modifier loop sets all modifiers to 1.0f (neutral) since
 * memset zeroed them to 0.0f which would mean "no decay at all".
 */
void game_new(void) {
    memset(&g_game, 0, sizeof(game_t));        /* zero the entire game state */
    g_game.state = GAME_STATE_ACTIVE;

    /* Initialize each subsystem with proper starting values */
    stat_init(&g_game.stats);
    emotion_init(&g_game.emotion);
    life_init(&g_game.life);
    progression_init(&g_game.progression);
    dialogue_init(&g_game.dialogue);
    ui_init(&g_game.ui);

    /* Initialize modifiers to sensible defaults.
     * 1.0f = neutral (no speed-up or slow-down on decay).
     * We must do this explicitly because memset set them to 0.0f. */
    for (int i = 0; i < MOD_COUNT; i++) {
        g_game.modifiers.values[i] = 1.0f;
    }

    /* Start in egg stage with immediate hatch for testing.
     * Set hatch_progress to 90 so a few interactions hatch it. */
    g_game.life.hatch_progress = 90;

    /* Initial dialogue -- shown on screen when game starts */
    dialogue_force(&g_game.dialogue, "An egg appears! Interact to hatch it.", 10000);
    ui_mark_dirty();  /* tell the renderer to redraw on next frame */
}

/*
 * game_loop_init -- One-time initialization of the entire game engine.
 *
 * Parameters: none
 * Returns:    nothing
 *
 * Called once at boot. Sets up all subsystems, registers event listeners,
 * creates a new game, and takes an initial sensor reading.
 *
 * The event_listen() calls establish the observer pattern: when an event
 * fires (e.g. EVENT_FED), the registered handler function
 * (e.g. emotion_on_care_action) is called automatically. This decouples
 * the stat system from the emotion system -- they communicate via events.
 */
void game_loop_init(void) {
    /* Initialize subsystems */
    time_mgr_init();
    event_init();
    sensor_init();
    input_init();

    /* Register event listeners.
     * This wires up the observer pattern: when event_fire(EVENT_FED, ...)
     * is called (from stat.c), it will automatically call
     * emotion_on_care_action() (in emotion.c). Neither module needs to
     * know about the other directly. */
    event_listen(EVENT_FED,     emotion_on_care_action);
    event_listen(EVENT_PETTED,  emotion_on_care_action);
    event_listen(EVENT_PLAYED,  emotion_on_care_action);
    event_listen(EVENT_SCOLDED, emotion_on_care_action);
    event_listen(EVENT_CLEANED, emotion_on_care_action);

    event_listen(EVENT_STEP_MILESTONE, progression_on_step_milestone);

    /* Create new game */
    game_new();

    /* Initialize sensor context.
     * Take one reading now so prev_sensor_ctx has valid data for the first
     * comparison in game_loop_tick(). Without this, the first delta
     * comparison would be against zeroed-out data. */
    prev_sensor_ctx = sensor_poll(0);  /* struct copy: copies all sensor fields */
    g_game.sensor = prev_sensor_ctx;   /* also a struct copy into g_game */
}

/* ─── State Transitions ──────────────────────────────────────── */

/*
 * game_state_transition -- Change the game's current state.
 *
 * Parameters:
 *   new_state -- The state to transition to (e.g. GAME_STATE_SLEEPING).
 *
 * Returns: nothing
 *
 * If we're already in the requested state, do nothing (avoid redundant
 * redraws). Otherwise, update the state and mark the UI dirty so the
 * screen reflects the new state on the next render pass.
 */
void game_state_transition(game_state_t new_state) {
    if (g_game.state == new_state) return;  /* no-op if already in this state */
    g_game.state = new_state;
    ui_mark_dirty();  /* trigger a redraw */
}

/* ─── Core Game Tick ─────────────────────────────────────────── */

/*
 * game_tick -- The core 1-second game tick. Runs all gameplay logic.
 *
 * Parameters:
 *   now_ms -- Current time in milliseconds.
 *   ctx    -- Pointer to the current sensor readings.
 *
 * Returns: nothing
 *
 * This function is the heart of the game. It runs once per second and
 * dispatches to different subsystems depending on the current game state.
 *
 * Not every subsystem runs every tick. The should_tick() helper uses
 * modulo to check if this tick number is a multiple of the subsystem's
 * rate. For example, TICK_RATE_EMOTION = 5 means emotion_resolve()
 * only runs every 5th tick (every 5 seconds). This is a common embedded
 * pattern to spread work across frames and save CPU.
 *
 * should_tick(tick_count, rate) expands to: (tick_count % rate) == 0
 *   tick_count=10, rate=5: 10 % 5 = 0, returns true
 *   tick_count=11, rate=5: 11 % 5 = 1, returns false
 */
void game_tick(uint32_t now_ms, sensor_context_t *ctx) {
    g_game.tick_count++;

    /* Update time -- converts raw ms to hour/minute/second/day */
    g_game.time = time_mgr_update(now_ms);  /* struct copy of the return value */

    /* Age tracking: sync the age field with the life module's counter */
    g_game.stats.secondary.age_seconds = g_game.life.age_seconds;

    switch (g_game.state) {
    case GAME_STATE_ACTIVE:
        /* 1. Stat decay every tick (TICK_RATE_STAT_DECAY = 1 means every tick) */
        if (should_tick(g_game.tick_count, TICK_RATE_STAT_DECAY)) {
            stat_decay_tick(&g_game.stats, &g_game.decay_accum,
                            &g_game.modifiers, g_game.state);
        }

        /* 2. Check stat thresholds -- fires events when stats go critical */
        stat_check_thresholds(&g_game.stats);

        /* 3. Life stage check -- may advance from egg to hatchling, etc. */
        life_stage_check(&g_game.life, &g_game.stats, ctx, &g_game.time);

        /* 4. Misbehavior check -- every 60 seconds (TICK_RATE_MISBEHAVIOR) */
        if (should_tick(g_game.tick_count, TICK_RATE_MISBEHAVIOR)) {
            misbehavior_check(&g_game.life, &g_game.stats, now_ms);
        }

        /* 5. Emotion resolution -- every 5 seconds (TICK_RATE_EMOTION) */
        if (should_tick(g_game.tick_count, TICK_RATE_EMOTION)) {
            emotion_resolve(&g_game.emotion, &g_game.stats, ctx, &g_game.life);
        }

        /* 6. Modifier recalculation -- every 10 seconds (TICK_RATE_MODIFIER) */
        if (should_tick(g_game.tick_count, TICK_RATE_MODIFIER)) {
            modifier_recalculate(&g_game.modifiers, &g_game.stats,
                                 &g_game.life, ctx, &g_game.time);
        }

        /* 7. Dialogue triggers -- every 30 seconds (TICK_RATE_DIALOGUE) */
        if (should_tick(g_game.tick_count, TICK_RATE_DIALOGUE)) {
            dialogue_check_triggers(&g_game.dialogue, &g_game.emotion,
                                    &g_game.stats, &g_game.time);
        }
        break;

    case GAME_STATE_MENU:
        /* Stats still decay in menus -- pausing decay would let players
         * exploit menu time to avoid caring for their creature. */
        stat_decay_tick(&g_game.stats, &g_game.decay_accum,
                        &g_game.modifiers, g_game.state);
        break;

    case GAME_STATE_SLEEPING:
        /* During sleep, only energy regenerates (via stat_sleep_tick).
         * Normal stat decay is paused. */
        stat_sleep_tick(&g_game.stats);

        /* Check wake triggers: sudden light increase or being picked up.
         * ctx->light.delta_lux > 300 means "lights came on" (e.g. morning).
         * ctx->accel.picked_up means the accelerometer detected lifting. */
        if (ctx->light.delta_lux > 300.0f || ctx->accel.picked_up) {
            game_state_transition(GAME_STATE_ACTIVE);
            event_fire(EVENT_WAKE_UP, NULL);  /* NULL data: no extra info needed */
        }
        break;

    default:
        break;  /* other states (BOOT, HUNT, EVENT, DEAD) have no tick logic yet */
    }

    /* Cooldown tick -- decrement all care action cooldowns by 1 */
    stat_cooldown_tick(&g_game.care_cd);

    /* Dialogue auto-dismiss -- checks if the current dialogue has timed out */
    dialogue_tick(&g_game.dialogue, now_ms);

    /* Mark dirty if emotion or dialogue changed -- so the UI redraws.
     * After checking, clear the flags so they don't trigger again next tick. */
    if (g_game.emotion.changed || g_game.dialogue.pending) {
        ui_mark_dirty();
    }
    g_game.emotion.changed = false;    /* clear the one-shot flag */
    g_game.dialogue.pending = false;   /* clear the one-shot flag */
}

/* ─── Main Loop Tick ─────────────────────────────────────────── */

/*
 * game_loop_tick -- Called every frame by the platform (hardware or emulator).
 *
 * Parameters:
 *   now_ms -- Current platform time in milliseconds.
 *
 * Returns: nothing
 *
 * This is the outermost entry point that the platform calls. It handles:
 *   1. Syncing the time manager to the platform clock
 *   2. Draining the button input queue
 *   3. Polling sensors and classifying sensor events
 *   4. Running the 1-second game tick (when enough time has passed)
 *   5. Rendering the screen (only if something changed)
 *
 * This function may be called much more frequently than once per second
 * (e.g. 30-60 Hz in the emulator). The game tick only fires when
 * TICK_INTERVAL_MS (1000ms) has elapsed since the last tick.
 */
void game_loop_tick(uint32_t now_ms) {
    time_mgr_set_ms(now_ms);  /* sync the time manager to the platform clock */

    /* Process queued button input.
     * Buttons are queued by an interrupt handler (on hardware) or by the
     * emulator's input system. We drain the entire queue here so no
     * button presses are lost. */
    while (input_has_event()) {
        button_event_t btn = input_poll();  /* dequeue one button event */
        ui_handle_input(btn);               /* pass to the UI state machine */
    }

    /* Poll sensors -- reads accelerometer, light, temp/humidity, mic.
     * Returns a sensor_context_t struct by value (copied onto the stack). */
    sensor_context_t ctx = sensor_poll(now_ms);

    /* Classify sensor events (compare current vs previous).
     * This detects changes like "picked up", "dropped", "loud noise"
     * by comparing current readings against the previous frame's readings.
     * After classification, save the current reading as the new "previous". */
    sensor_classify_events(&prev_sensor_ctx, &ctx);
    prev_sensor_ctx = ctx;   /* struct assignment: copies all fields */
    g_game.sensor = ctx;     /* also keep a copy in the global game state */

    /* Game tick at 1-second intervals.
     * The subtraction `now_ms - g_game.last_tick_ms` gives the time
     * elapsed since the last game tick. When it exceeds TICK_INTERVAL_MS
     * (1000ms), we run a tick and update the timestamp. */
    if (now_ms - g_game.last_tick_ms >= TICK_INTERVAL_MS) {
        g_game.last_tick_ms = now_ms;
        game_tick(now_ms, &ctx);  /* &ctx: pass pointer to the local struct */
    }

    /* Render if dirty -- only redraws the screen when ui_mark_dirty()
     * was called (by a state change, emotion change, dialogue, etc.).
     * This avoids wasting CPU/power on redundant screen updates. */
    if (ui_needs_redraw()) {
        ui_render();
    }
}
