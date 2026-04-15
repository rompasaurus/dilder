/*
 * progress.c -- Bond Progression System
 *
 * This module tracks the bond between the player and the Dilder creature.
 * As the player cares for the creature, bond XP accumulates and the bond
 * "level" increases through named tiers (Stranger -> Acquaintance ->
 * Companion -> Friend -> Best Friend -> Soulmate).
 *
 * Key concepts used in this file:
 *   - Designated initializer arrays: BOND_THRESHOLDS uses [ENUM_VALUE] = X
 *     syntax to map enum indices to threshold values.
 *   - extern: used to reference the global game state (g_game) defined in
 *     another translation unit.
 *   - Compound literals: (event_data_t){ .value = X } creates a temporary
 *     struct on the stack to pass event data.
 *   - (void) casts: explicitly silence "unused parameter" compiler warnings.
 *   - Reverse iteration: the level calculation loop starts from the highest
 *     level and works down, returning the first match.
 */

#include "game/progress.h"
#include "game/event.h"

/* ─── Bond XP Thresholds ─────────────────────────────────────────
 *
 * This array maps each bond_level_t enum value to the minimum bond XP
 * required to reach that level.
 *
 * `static const` means:
 *   - static: private to this file (other .c files can't see it)
 *   - const: the values can't be modified at runtime
 *   Together, the compiler places this in the read-only data segment
 *   (.rodata), which on embedded systems typically lives in flash rather
 *   than RAM.
 *
 * The [BOND_STRANGER] = 0 syntax is a "designated initializer" (C99).
 * Instead of listing values in positional order, you name the index
 * explicitly. This makes the mapping self-documenting and resilient to
 * enum reordering. Any unmentioned indices are automatically set to 0.
 *
 * BOND_XP_ACQUAINTANCE, BOND_XP_COMPANION, etc. are constants defined
 * in the header file (progress.h).
 */
static const uint32_t BOND_THRESHOLDS[] = {
    [BOND_STRANGER]      = 0,
    [BOND_ACQUAINTANCE]  = BOND_XP_ACQUAINTANCE,
    [BOND_COMPANION]     = BOND_XP_COMPANION,
    [BOND_FRIEND]        = BOND_XP_FRIEND,
    [BOND_BEST_FRIEND]   = BOND_XP_BEST_FRIEND,
    [BOND_SOULMATE]      = BOND_XP_SOULMATE,
};

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * progression_init -- Initialize the progression state to defaults.
 *
 * Parameters:
 *   prog -- pointer to the progression_t struct to initialize.
 *           The caller owns this memory (it's part of the game struct).
 *
 * memset zeroes all bytes (bond_xp=0, etc.), then we explicitly set the
 * starting bond level. sizeof(*prog) means "size of the thing prog
 * points to" -- this automatically matches the correct struct size.
 */
void progression_init(progression_t *prog) {
    memset(prog, 0, sizeof(*prog));
    prog->bond_level = BOND_STRANGER;
}

/*
 * progression_calc_level -- Determine the bond level for a given XP amount.
 *
 * Parameters:
 *   bond_xp -- the total bond experience points accumulated
 *
 * Returns: the highest bond_level_t whose threshold is <= bond_xp.
 *
 * The loop iterates BACKWARDS from the highest level (BOND_COUNT - 1)
 * down to 0. This way, the first match is always the highest applicable
 * level. For example, if bond_xp is 5000 and the thresholds are
 * [0, 100, 500, 2000, 5000, 10000], it would match index 4 (5000)
 * on the first qualifying iteration rather than index 0 (0).
 *
 * (bond_level_t)i -- casts the integer loop variable back to the enum
 * type. In C, enums are just integers under the hood, but the cast
 * makes the return type match the function signature and communicates
 * intent to the reader.
 */
bond_level_t progression_calc_level(uint32_t bond_xp) {
    for (int i = BOND_COUNT - 1; i >= 0; i--) {
        if (bond_xp >= BOND_THRESHOLDS[i]) {
            return (bond_level_t)i;  /* cast int to enum type */
        }
    }
    return BOND_STRANGER;  /* fallback (should never reach here since threshold[0] = 0) */
}

/*
 * progression_add_xp -- Add bond experience points and check for level-up.
 *
 * Parameters:
 *   prog   -- mutable pointer to the progression state
 *   amount -- how much XP to add (uint16_t, max 65535 per call)
 *
 * If the XP addition causes a level-up, fires an EVENT_BOND_LEVEL_UP
 * event so other systems (UI, dialog, achievements) can react.
 */
void progression_add_xp(progression_t *prog, uint16_t amount) {
    prog->bond_xp += amount;

    bond_level_t new_level = progression_calc_level(prog->bond_xp);
    if (new_level > prog->bond_level) {
        prog->bond_level = new_level;
        /*
         * Fire a level-up event. The compound literal:
         *   (event_data_t){ .value = new_level }
         * creates a temporary event_data_t struct on the stack with its
         * .value field set to new_level. The & takes its address so we
         * can pass a pointer to event_fire(). The temporary exists until
         * the end of this statement -- long enough for event_fire() to
         * read the data.
         */
        event_fire(EVENT_BOND_LEVEL_UP, &(event_data_t){
            .value = new_level
        });
    }
}

/* ─── Event Handlers ─────────────────────────────────────────────
 *
 * These functions are registered as listeners with the event system.
 * When specific events fire, the event system calls these callbacks.
 */

/*
 * progression_on_care_action -- Called when any care action event fires.
 *
 * Parameters:
 *   type -- which event fired (EVENT_FED, EVENT_PETTED, etc.)
 *   data -- optional extra data for the event (unused here)
 *
 * Currently a placeholder: XP is already added by the stat system
 * (stat_apply_care). This handler exists for future side-effects
 * like achievement tracking.
 *
 * The (void)type and (void)data lines are a C idiom for silencing
 * "unused parameter" compiler warnings. Casting to (void) tells the
 * compiler "yes, I know I'm not using this -- that's intentional."
 * Without these, compiling with -Wunused-parameter (common in
 * embedded projects) would produce warnings.
 */
void progression_on_care_action(event_type_t type, const event_data_t *data) {
    /* XP already added by stat_apply_care. This handler is for
     * additional progression side-effects (achievements, etc.) */
    (void)type;
    (void)data;
}

/*
 * progression_on_step_milestone -- Called when the player hits a step-count
 * milestone (detected by the accelerometer/pedometer).
 *
 * Parameters:
 *   type -- the event type (EVENT_STEP_MILESTONE)
 *   data -- optional event data (unused here)
 *
 * Awards 20 bond XP as a reward for physical activity.
 *
 * `extern game_t g_game` tells the compiler that g_game is a global
 * variable of type game_t defined in another .c file. The `extern`
 * keyword means "this exists somewhere else -- don't allocate new
 * storage, just let me reference it." g_game is the single global
 * game state that contains all subsystems (stats, emotion, life,
 * progression, etc.). Declaring it inside the function limits its
 * visibility scope to just this function body.
 */
void progression_on_step_milestone(event_type_t type, const event_data_t *data) {
    extern game_t g_game;
    progression_add_xp(&g_game.progression, 20);
}
