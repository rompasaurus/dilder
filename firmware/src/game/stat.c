/*
 * stat.c -- Creature stat management, decay, care actions, and modifiers
 *
 * This is the largest gameplay module. It handles:
 *   1. Stat initialization (hunger, happiness, energy, hygiene, health)
 *   2. Stat decay over time (stats gradually decrease each tick)
 *   3. Health computation (derived from how many other stats are critical)
 *   4. Threshold monitoring (fires events when stats drop too low or recover)
 *   5. Care actions (feeding, cleaning, playing, etc. -- the player's inputs)
 *   6. Modifier recalculation (environmental/life-stage multipliers on decay)
 *   7. Offline decay (catch-up when the device was off)
 *   8. Query helpers (get stat by ID, check if critical, check if balanced)
 *
 * Memory model:
 *   - The stats_t struct itself lives inside g_game (the global game struct)
 *     in the BSS segment. Pointers to it are passed into these functions.
 *   - The CARE_EFFECTS table and STAGE_MODS table are "static const" --
 *     they're stored in read-only memory (the .rodata section on most
 *     platforms) and never change at runtime.
 *   - The `thresholds` array is static (file-scope) and mutable because
 *     each entry has a `fired` flag that toggles at runtime.
 *   - Several functions use `static` local variables (health_decay_ctr,
 *     health_regen_ctr, sleep_regen_ctr) -- these persist across calls
 *     instead of being re-created on the stack each time.
 *   - No heap allocation (malloc/free) is used anywhere.
 *
 * Key C concepts:
 *   - Designated initializers: `[CARE_FEED_MEAL] = { ... }` to init
 *     array elements by enum index instead of sequential order
 *   - Compound literals: `(event_data_t){ .stat_id = ..., .value = ... }`
 *     to create a temporary struct on the stack inline
 *   - Fixed-point arithmetic: decay rates are stored x1000 to avoid floats
 *     for the accumulation, then divided back out via a threshold
 *   - Static local variables: persist across function calls (like globals
 *     but scoped to one function)
 *   - sizeof(array) / sizeof(array[0]): classic C idiom to get array length
 */

#include "game/stat.h"
#include "game/event.h"
#include "game/time_mgr.h"
#include <math.h>

/* ─── Base Decay Rates (per 600 ticks, x1000 fixed-point) ──── */
/*
 * These #defines control how fast each stat drops over time.
 * They use a "fixed-point" technique: instead of storing 1.0 as a float,
 * we store 1000 as an integer. This avoids float rounding during accumulation.
 *
 * "per 600 ticks" means: over 600 game ticks (= 10 minutes at 1 tick/sec),
 * this much decay accumulates.
 *
 * Example: HUNGER_DECAY_PER_600 = 1000 means hunger drops 1.000 points
 * every 10 minutes. HAPPINESS_DECAY_PER_600 = 667 means happiness drops
 * 0.667 points every 10 minutes.
 */
#define HUNGER_DECAY_PER_600    1000   /* 1.000 per 10 min */
#define HAPPINESS_DECAY_PER_600  667   /* 0.667 per 10 min */
#define ENERGY_DECAY_PER_600     833   /* 0.833 per 10 min */
#define HYGIENE_DECAY_PER_600    333   /* 0.333 per 10 min */

/*
 * DECAY_THRESHOLD -- When an accumulator reaches this value, one stat
 * point is subtracted and the accumulator is reduced by this amount.
 * 600000 = 600 ticks * 1000 (the fixed-point scale).
 * This means accumulators "overflow" once per 600 ticks at base rate.
 */
#define DECAY_THRESHOLD 600000

/* ─── Care Effects Table ─────────────────────────────────────── */
/*
 * This struct defines what happens when the player performs a care action.
 * Each field is the delta (change) applied to the corresponding stat.
 * Negative values decrease the stat; positive values increase it.
 *
 * bond_xp:            How much bond experience the action awards.
 * requires_condition: If true, the action can only be used when a
 *                     specific condition is met (e.g. medicine requires
 *                     health < 30).
 * cooldown_ticks:     How many ticks before this action can be used again.
 */
typedef struct {
    int8_t  hunger, happiness, energy, hygiene, health, weight;
    uint8_t bond_xp;
    bool    requires_condition;
    uint16_t cooldown_ticks;
} care_effect_t;

/*
 * CARE_EFFECTS -- Lookup table mapping each care_action_t enum to its effects.
 *
 * "static const" means:
 *   - static: visible only within this file (internal linkage)
 *   - const: read-only; the compiler may place this in flash/ROM
 *
 * The [CARE_FEED_MEAL] = { ... } syntax is a "designated initializer":
 * it lets you set array elements by their enum value rather than by
 * sequential index. This is safer than positional initialization because
 * reordering the enum won't silently break the table.
 */
static const care_effect_t CARE_EFFECTS[CARE_COUNT] = {
    /*                     hun  hap  ene  hyg  hea  wgt  xp   cond  cd  */
    [CARE_FEED_MEAL]   = { 30,   0,   0,   0,   0,   1,  5, false, 30 },
    [CARE_FEED_SNACK]  = { 10,  15,   0,   0,   0,   2,  3, false, 15 },
    [CARE_FEED_TREAT]  = {  5,  25,   0,   0,   0,   3, 10, false, 60 },
    [CARE_CLEAN]       = {  0,   0,   0,  40,   0,   0,  5, false, 60 },
    [CARE_MEDICINE]    = {  0,   0,   0,   0,  20,   0,  5, true, 120 },
    [CARE_PET]         = {  0,  10,   0,   0,   0,   0,  2, false,  5 },
    [CARE_PLAY]        = {  0,  20, -10,   0,   0,  -1, 10, false, 30 },
    [CARE_TICKLE]      = {  0,   5,   0,   0,   0,   0,  1, false,  3 },
    [CARE_SCOLD]       = {  0,   0,   0,   0,   0,   0,  0, false, 30 },
    [CARE_SLEEP_TOGGLE]= {  0,   0,   0,   0,   0,   0,  0, false, 10 },
};

/* ─── Threshold Checks ───────────────────────────────────────── */
/*
 * threshold_check_t -- Defines a "watch" on a stat: when the stat drops
 * to or below `threshold`, fire the specified event.
 *
 * The `fired` flag prevents the event from firing repeatedly every tick.
 * Once the stat recovers (rises above threshold + 10), `fired` resets
 * and the threshold can trigger again.
 */
typedef struct {
    stat_id_t    stat_id;
    int16_t      threshold;
    event_type_t event;
    bool         fired;      /* has this threshold already triggered? */
} threshold_check_t;

/*
 * thresholds -- Array of all stat thresholds to monitor.
 *
 * This is "static" (file-scope) but NOT "const" because the `fired` field
 * changes at runtime. It lives in the BSS/data segment.
 *
 * Two tiers of thresholds are defined:
 *   - EVENT_STAT_CRITICAL: fires when a stat is dangerously low
 *   - EVENT_STAT_ZERO: fires when a stat hits absolute zero
 */
static threshold_check_t thresholds[] = {
    { STAT_HUNGER,    20, EVENT_STAT_CRITICAL, false },
    { STAT_HAPPINESS, 20, EVENT_STAT_CRITICAL, false },
    { STAT_ENERGY,    15, EVENT_STAT_CRITICAL, false },
    { STAT_HYGIENE,   25, EVENT_STAT_CRITICAL, false },
    { STAT_HEALTH,    30, EVENT_STAT_CRITICAL, false },
    { STAT_HUNGER,     0, EVENT_STAT_ZERO,     false },
    { STAT_HAPPINESS,  0, EVENT_STAT_ZERO,     false },
    { STAT_ENERGY,     0, EVENT_STAT_ZERO,     false },
};

/*
 * NUM_THRESHOLDS -- Number of entries in the thresholds array.
 *
 * sizeof(thresholds) gives the total size in bytes of the entire array.
 * sizeof(thresholds[0]) gives the size of one element.
 * Dividing gives the element count. This is a standard C idiom that
 * automatically stays correct if you add or remove entries.
 */
#define NUM_THRESHOLDS (sizeof(thresholds) / sizeof(thresholds[0]))

/* ─── Implementation ─────────────────────────────────────────── */

/*
 * stat_init -- Initialize all creature stats to their starting values.
 *
 * Parameters:
 *   stats -- Pointer to the stats_t struct to initialize (inside g_game).
 *
 * Returns: nothing
 *
 * Uses compound literals (the `(primary_stats_t){ ... }` syntax) to create
 * a temporary struct value on the stack with the desired field values,
 * then assigns (copies) it into the target. This is cleaner than setting
 * each field individually.
 *
 * The creature starts at half hunger/happiness, full energy/hygiene/health,
 * zero bond, and normal weight (100 = baseline).
 *
 * Also resets all threshold fire states so they can trigger fresh.
 */
void stat_init(stats_t *stats) {
    /* Compound literal: creates a temporary primary_stats_t on the stack,
     * then copies it into stats->primary via struct assignment. */
    stats->primary = (primary_stats_t){
        .hunger = 50, .happiness = 50, .energy = 100,
        .hygiene = 100, .health = 100,
    };
    stats->secondary = (secondary_stats_t){
        .bond_xp = 0, .discipline = 0, .intelligence = 0,
        .fitness = 0, .exploration = 0, .age_seconds = 0, .weight = 100,
    };
    memset(&stats->hidden, 0, sizeof(hidden_stats_t));  /* zero all hidden stats */

    /* Reset threshold fire states */
    for (size_t i = 0; i < NUM_THRESHOLDS; i++) {
        thresholds[i].fired = false;
    }
}

/*
 * stat_clamp_all -- Constrain all primary stats to the range [0, 100].
 *
 * Parameters:
 *   stats -- Pointer to the primary_stats_t to clamp.
 *
 * Returns: nothing
 *
 * clamp_i16(val, 0, 100) returns:
 *   - 0   if val < 0
 *   - 100 if val > 100
 *   - val otherwise
 * This prevents stats from going negative or exceeding 100 after
 * additions/subtractions. Called after nearly every stat modification.
 */
void stat_clamp_all(primary_stats_t *stats) {
    stats->hunger    = clamp_i16(stats->hunger,    0, 100);
    stats->happiness = clamp_i16(stats->happiness, 0, 100);
    stats->energy    = clamp_i16(stats->energy,    0, 100);
    stats->hygiene   = clamp_i16(stats->hygiene,   0, 100);
    stats->health    = clamp_i16(stats->health,    0, 100);
}

/*
 * stat_update_health -- Derive health from how many other stats are critical.
 *
 * Parameters:
 *   stats -- Pointer to the full stats_t (needs both primary and secondary).
 *
 * Returns: nothing
 *
 * Logic:
 *   - 3+ stats critical: health drops by 1 every tick (fast decay)
 *   - 2 stats critical: health drops by 1 every 5 ticks (slow decay)
 *   - 0 critical + good hunger/happiness: health regenerates 1 every 30 ticks
 *
 * The static local variables `health_decay_ctr` and `health_regen_ctr`
 * are counters that persist across function calls. In C, a `static`
 * variable inside a function is allocated once (in BSS/data segment) and
 * keeps its value between calls -- unlike normal local variables which
 * are created on the stack and lost when the function returns.
 *
 * This is a simple way to implement "do something every Nth call" without
 * needing an external counter.
 */
void stat_update_health(stats_t *stats) {
    primary_stats_t *p = &stats->primary;  /* shorthand pointer to avoid typing stats->primary repeatedly */

    int critical_count = 0;
    if (p->hunger    < 20) critical_count++;
    if (p->happiness < 20) critical_count++;
    if (p->energy    < 15) critical_count++;
    if (p->hygiene   < 25) critical_count++;

    if (critical_count >= 3) {
        p->health -= 1;  /* fast health decay: every single tick */
    } else if (critical_count >= 2) {
        /* Slow decay: -1 every 5 ticks tracked via static counter.
         *
         * `static uint8_t health_decay_ctr = 0;`
         * This variable lives in BSS, NOT on the stack. It keeps its value
         * across calls. The `= 0` initializer only runs once (at program start),
         * not every time the function is called. */
        static uint8_t health_decay_ctr = 0;
        if (++health_decay_ctr >= 5) {  /* prefix ++: increment THEN compare */
            p->health -= 1;
            health_decay_ctr = 0;       /* reset counter after applying decay */
        }
    } else if (critical_count == 0 && p->hunger > 50 && p->happiness > 50) {
        /* Health regeneration: only when no stats are critical AND
         * the creature is well-fed and happy. */
        static uint8_t health_regen_ctr = 0;  /* also persists across calls */
        if (++health_regen_ctr >= 30) {
            p->health += 1;
            health_regen_ctr = 0;
        }
    }

    p->health = clamp_i16(p->health, 0, 100);
}

/*
 * stat_decay_tick -- Apply one tick of stat decay (called once per second).
 *
 * Parameters:
 *   stats -- Pointer to the creature's stats.
 *   accum -- Pointer to the decay accumulators (fractional buildup).
 *   mods  -- Pointer to the modifier stack (life stage, bond, environment, etc.).
 *   state -- Current game state (decay is skipped when sleeping).
 *
 * Returns: nothing
 *
 * How fixed-point decay works:
 *   Each tick, we add (base_rate * combined_modifier) to the accumulator.
 *   When the accumulator reaches DECAY_THRESHOLD (600000), we subtract 1
 *   from the actual stat and reduce the accumulator by DECAY_THRESHOLD.
 *
 *   This allows fractional decay: if the modifier slows decay to 0.5x,
 *   the accumulator fills up half as fast, and the stat takes twice as
 *   long to drop by 1 point.
 *
 *   The (uint32_t) cast truncates the float result to an integer before
 *   adding it to the accumulator. We lose the fractional part of each
 *   individual tick, but over many ticks the accumulation is close enough.
 */
void stat_decay_tick(stats_t *stats, decay_accum_t *accum,
                     const modifier_stack_t *mods, game_state_t state) {
    if (state == GAME_STATE_SLEEPING) return;  /* no decay while sleeping */

    /* Read individual modifier values from the modifier stack */
    float stage_mod    = mods->values[MOD_LIFE_STAGE];   /* baby = 2x, adult = 0.75x */
    float bond_mod     = mods->values[MOD_BOND_LEVEL];   /* higher bond = slower decay */
    float env_mod      = mods->values[MOD_ENVIRONMENT];   /* harsh env = faster decay */
    float tod_mod      = mods->values[MOD_TIME_OF_DAY];   /* daytime = faster decay */
    float activity_mod = mods->values[MOD_ACTIVITY];       /* walking = faster energy drain */

    /* Multiply all modifiers together for a single combined factor.
     * activity_mod is intentionally excluded here -- it only affects energy. */
    float combined = stage_mod * bond_mod * env_mod * tod_mod;

    /* Accumulate fractional decay.
     * (uint32_t)(...) casts the float product to an unsigned 32-bit integer,
     * truncating any fractional part. This is safe because the values are
     * always positive and well within uint32_t range. */
    accum->hunger_accum    += (uint32_t)(HUNGER_DECAY_PER_600 * combined);
    accum->happiness_accum += (uint32_t)(HAPPINESS_DECAY_PER_600 * combined);
    accum->energy_accum    += (uint32_t)(ENERGY_DECAY_PER_600 * combined * activity_mod);
    accum->hygiene_accum   += (uint32_t)(HYGIENE_DECAY_PER_600 * combined);

    /* Subtract 1 stat point when accumulator overflows threshold.
     * We use `-=` instead of `= 0` so any overshoot carries forward,
     * keeping the long-term average accurate. */
    if (accum->hunger_accum >= DECAY_THRESHOLD) {
        stats->primary.hunger -= 1;
        accum->hunger_accum -= DECAY_THRESHOLD;
    }
    if (accum->happiness_accum >= DECAY_THRESHOLD) {
        stats->primary.happiness -= 1;
        accum->happiness_accum -= DECAY_THRESHOLD;
    }
    if (accum->energy_accum >= DECAY_THRESHOLD) {
        stats->primary.energy -= 1;
        accum->energy_accum -= DECAY_THRESHOLD;
    }
    if (accum->hygiene_accum >= DECAY_THRESHOLD) {
        stats->primary.hygiene -= 1;
        accum->hygiene_accum -= DECAY_THRESHOLD;
    }

    stat_clamp_all(&stats->primary);  /* enforce 0-100 bounds */
    stat_update_health(stats);         /* recompute health from other stats */
}

/*
 * stat_sleep_tick -- Apply one tick of sleep effects (energy regeneration).
 *
 * Parameters:
 *   stats -- Pointer to the creature's stats.
 *
 * Returns: nothing
 *
 * Called every tick while the creature is sleeping. Energy slowly
 * regenerates. The static counter `sleep_regen_ctr` ensures we only
 * add 1 energy every 30 ticks (30 seconds), not every single tick.
 */
void stat_sleep_tick(stats_t *stats) {
    /* Energy regenerates during sleep.
     *
     * static: this counter persists between calls (see stat_update_health
     * comments for a detailed explanation of static local variables). */
    static uint8_t sleep_regen_ctr = 0;
    if (++sleep_regen_ctr >= 30) {       /* every 30 ticks... */
        stats->primary.energy += 1;      /* ...gain 1 energy point */
        sleep_regen_ctr = 0;
    }
    stats->primary.energy = clamp_i16(stats->primary.energy, 0, 100);
}

/*
 * stat_check_thresholds -- Scan all stat thresholds and fire events as needed.
 *
 * Parameters:
 *   stats -- Pointer to the creature's stats.
 *
 * Returns: nothing
 *
 * For each threshold entry:
 *   - If the stat is at or below the threshold and we haven't fired yet,
 *     fire the event and mark it fired.
 *   - If the stat has recovered above threshold + 10 and we previously
 *     fired, reset the flag and fire a recovery event.
 *   - The +10 hysteresis prevents rapid on/off toggling when a stat
 *     hovers right at the threshold.
 *
 * Also tracks "care mistakes": if any stat has been critical for 15+
 * minutes (15 * 60 * 1000 ms) without being addressed, that counts as
 * a care mistake (hidden stat used for evolution calculations).
 */
void stat_check_thresholds(stats_t *stats) {
    for (size_t i = 0; i < NUM_THRESHOLDS; i++) {
        threshold_check_t *tc = &thresholds[i];  /* pointer to current entry */
        int16_t value = stat_get_by_id(&stats->primary, tc->stat_id);

        if (value <= tc->threshold && !tc->fired) {
            tc->fired = true;
            /*
             * &(event_data_t){ .stat_id = ..., .value = ... }
             *
             * This is taking the address of a compound literal.
             * The compound literal creates a temporary event_data_t on the stack,
             * and `&` gives us a pointer to it. The pointer is valid for the
             * duration of this statement (the event_fire call). This avoids
             * needing to declare a separate local variable.
             */
            event_fire(tc->event, &(event_data_t){
                .stat_id = tc->stat_id, .value = value
            });

            if (tc->event == EVENT_STAT_CRITICAL) {
                stats->hidden.neglect_timer_ms = time_mgr_now_ms();  /* start neglect timer */
            }
        } else if (value > tc->threshold + 10 && tc->fired) {
            /* Stat recovered: reset fired flag, fire recovery event.
             * The +10 is hysteresis: the stat must rise 10 points ABOVE
             * the threshold before we consider it "recovered". This prevents
             * rapid toggling when the stat is right at the boundary. */
            tc->fired = false;
            event_fire(EVENT_STAT_RECOVERED, &(event_data_t){
                .stat_id = tc->stat_id, .value = value
            });
            stats->hidden.neglect_timer_ms = 0;  /* clear neglect timer */
        }
    }

    /* Care mistake tracking.
     * If the neglect timer is active (> 0), check how long it's been.
     * 15 * 60 * 1000 = 900,000 ms = 15 minutes.
     * If 15 minutes have passed with a critical stat unaddressed,
     * increment the care_mistakes counter and restart the timer. */
    if (stats->hidden.neglect_timer_ms > 0) {
        uint32_t elapsed = time_mgr_now_ms() - stats->hidden.neglect_timer_ms;
        if (elapsed >= 15 * 60 * 1000) {           /* 15 minutes in ms */
            stats->hidden.care_mistakes++;          /* permanent hidden penalty */
            stats->hidden.neglect_timer_ms = time_mgr_now_ms();  /* restart timer */
        }
    }
}

/*
 * stat_apply_care -- Apply a care action (feed, clean, play, etc.) to the creature.
 *
 * Parameters:
 *   stats       -- Pointer to the creature's stats.
 *   cd          -- Pointer to the cooldown tracker for care actions.
 *   action      -- Which care action to perform (enum care_action_t).
 *   misbehaving -- Whether the creature is currently misbehaving (affects scold).
 *
 * Returns: nothing
 *
 * Flow:
 *   1. Bounds-check the action enum.
 *   2. Look up the care_effect_t from the CARE_EFFECTS table.
 *   3. Check if the action is on cooldown -- if so, reject it.
 *   4. Set the cooldown timer for this action.
 *   5. Check if the action has a prerequisite condition.
 *   6. Handle CARE_SCOLD specially (it has branching behavior).
 *   7. Apply all stat deltas from the effect table.
 *   8. Clamp stats to valid range.
 *   9. Fire an appropriate event so other systems (emotions, progression) react.
 */
void stat_apply_care(stats_t *stats, care_cooldown_t *cd,
                     care_action_t action, bool misbehaving) {
    if (action >= CARE_COUNT) return;  /* invalid action index guard */

    const care_effect_t *fx = &CARE_EFFECTS[action];  /* pointer into the const table */

    /* Check cooldown: if the timer for this action is still counting down, reject */
    if (cd->cooldowns[action] > 0) return;
    cd->cooldowns[action] = fx->cooldown_ticks;  /* start the cooldown timer */

    /* Medicine requires health < 30 -- the `requires_condition` flag */
    if (fx->requires_condition && stats->primary.health >= 30) return;

    /* Scold: special handling -- behavior depends on whether creature is misbehaving */
    if (action == CARE_SCOLD) {
        if (misbehaving) {
            /* Correct scolding: discipline goes up, fire event with value=1 */
            stats->secondary.discipline += 25;
            stats->secondary.discipline = clamp_u16(stats->secondary.discipline, 0, 100);
            event_fire(EVENT_SCOLDED, &(event_data_t){ .value = 1 });  /* 1 = justified */
        } else {
            /* Unjustified scolding: happiness drops, bond decreases */
            stats->primary.happiness -= 10;
            if (stats->secondary.bond_xp > 5)
                stats->secondary.bond_xp -= 5;  /* guard against unsigned underflow */
            event_fire(EVENT_SCOLDED, &(event_data_t){ .value = 0 });  /* 0 = unjustified */
        }
        stat_clamp_all(&stats->primary);
        stats->hidden.last_interaction_ms = time_mgr_now_ms();
        return;  /* scold is fully handled, skip the generic effect application */
    }

    /* Apply effects from the lookup table.
     * Each field in the care_effect_t is an additive delta: positive values
     * increase the stat, negative values decrease it. For example,
     * CARE_PLAY has energy = -10 (playing is tiring) and weight = -1. */
    stats->primary.hunger    += fx->hunger;
    stats->primary.happiness += fx->happiness;
    stats->primary.energy    += fx->energy;
    stats->primary.hygiene   += fx->hygiene;
    stats->primary.health    += fx->health;
    stats->secondary.weight  += fx->weight;
    stats->secondary.bond_xp += fx->bond_xp;

    stat_clamp_all(&stats->primary);
    stats->secondary.weight = clamp_i16(stats->secondary.weight, 50, 150);  /* weight range: 50-150 */

    stats->hidden.last_interaction_ms = time_mgr_now_ms();  /* record interaction time */

    /* Fire appropriate care event based on action category.
     *
     * action <= CARE_FEED_TREAT: this works because the feeding actions
     * are the first 3 enum values (0, 1, 2). All feeding actions fire
     * EVENT_FED with the specific action as the value. */
    if (action <= CARE_FEED_TREAT) {
        event_fire(EVENT_FED, &(event_data_t){ .value = action });
    } else if (action == CARE_PET) {
        event_fire(EVENT_PETTED, &(event_data_t){ .value = 0 });
    } else if (action == CARE_CLEAN) {
        event_fire(EVENT_CLEANED, &(event_data_t){ .value = 0 });
    } else if (action == CARE_PLAY || action == CARE_TICKLE) {
        event_fire(EVENT_PLAYED, &(event_data_t){ .value = action });
    }
}

/*
 * stat_cooldown_tick -- Decrement all active care cooldown timers by 1.
 *
 * Parameters:
 *   cd -- Pointer to the care_cooldown_t struct holding all cooldown timers.
 *
 * Returns: nothing
 *
 * Called once per second. Each cooldown that's above 0 ticks down by 1.
 * When a cooldown reaches 0, the corresponding care action becomes available.
 */
void stat_cooldown_tick(care_cooldown_t *cd) {
    for (int i = 0; i < CARE_COUNT; i++) {
        if (cd->cooldowns[i] > 0) cd->cooldowns[i]--;  /* tick down toward zero */
    }
}

/* ─── Modifier Recalculation ─────────────────────────────────── */

/*
 * STAGE_MODS -- Decay rate multiplier for each life stage.
 *
 * These control how fast stats decay relative to the base rate:
 *   0.0 = no decay (egg doesn't need care)
 *   2.0 = double speed (hatchlings are needy!)
 *   0.6 = 60% speed (elders are low-maintenance)
 *
 * Designated initializer syntax: [LIFE_STAGE_EGG] = 0.0f
 * This ties each value to its enum constant, so the array stays correct
 * even if someone reorders the enum.
 */
static const float STAGE_MODS[] = {
    [LIFE_STAGE_EGG]        = 0.0f,
    [LIFE_STAGE_HATCHLING]  = 2.0f,
    [LIFE_STAGE_JUVENILE]   = 1.2f,
    [LIFE_STAGE_ADOLESCENT] = 1.0f,
    [LIFE_STAGE_ADULT]      = 0.75f,
    [LIFE_STAGE_ELDER]      = 0.6f,
};

/*
 * modifier_recalculate -- Recompute all gameplay modifiers from current state.
 *
 * Parameters:
 *   mods  -- Pointer to the modifier_stack_t to write results into.
 *   stats -- Current creature stats (used for bond level).
 *   life  -- Current life state (used for life stage).
 *   ctx   -- Current sensor readings (temperature, humidity, movement).
 *   gt    -- Current game time (used for time-of-day modifier).
 *
 * Returns: nothing
 *
 * Modifiers are multipliers that speed up or slow down stat decay.
 * A modifier of 1.0 = no effect. Above 1.0 = faster decay. Below 1.0 = slower.
 *
 * These are recalculated periodically (every TICK_RATE_MODIFIER ticks)
 * rather than every tick, since sensor data and life stage don't change
 * that fast. This saves CPU cycles.
 */
void modifier_recalculate(modifier_stack_t *mods, const stats_t *stats,
                          const life_state_t *life, const sensor_context_t *ctx,
                          const game_time_t *gt) {
    /* Life stage modifier.
     * Ternary: if the stage enum is valid, look up the table; otherwise default to 1.0.
     * This guards against an out-of-bounds array read. */
    mods->values[MOD_LIFE_STAGE] = (life->stage < LIFE_STAGE_COUNT)
        ? STAGE_MODS[life->stage] : 1.0f;

    /* Bond modifier: higher bond_xp = slightly slower decay (up to 15% reduction).
     *
     * bond_xp / 50000.0f normalizes bond XP to a 0.0-1.0 range (at 50,000 max).
     * Multiplying by 0.15 gives a 0-15% reduction.
     * Subtracting from 1.0 means: at 0 bond, factor=1.0; at max bond, factor=0.85.
     * fmaxf_safe clamps the result so it never goes below 0.85.
     */
    float bond_factor = 1.0f - (stats->secondary.bond_xp / 50000.0f) * 0.15f;
    mods->values[MOD_BOND_LEVEL] = fmaxf_safe(bond_factor, 0.85f);

    /* Environment modifier: comfortable conditions slow decay; extremes speed it up.
     * Based on real sensor data (temperature + humidity from the AHT20 sensor). */
    if (ctx->env.celsius >= 18.0f && ctx->env.celsius <= 24.0f &&
        ctx->env.humidity_pct >= 40.0f && ctx->env.humidity_pct <= 60.0f) {
        mods->values[MOD_ENVIRONMENT] = 0.9f;   /* comfortable: 10% slower decay */
    } else if (ctx->env.celsius > 28.0f || ctx->env.celsius < 15.0f) {
        mods->values[MOD_ENVIRONMENT] = 1.3f;   /* extreme temp: 30% faster decay */
    } else {
        mods->values[MOD_ENVIRONMENT] = 1.0f;   /* neutral: no modifier */
    }

    /* Time of day modifier: creatures are more active during daytime. */
    if (gt->hour >= 8 && gt->hour < 20) {
        mods->values[MOD_TIME_OF_DAY] = 1.2f;   /* daytime: 20% faster decay */
    } else {
        mods->values[MOD_TIME_OF_DAY] = 0.8f;   /* nighttime: 20% slower decay */
    }

    /* Activity modifier: physical movement (accelerometer detects steps)
     * increases energy drain. */
    if (ctx->accel.steps_since_last > 0) {
        mods->values[MOD_ACTIVITY] = 1.3f;      /* moving: 30% faster energy decay */
    } else {
        mods->values[MOD_ACTIVITY] = 1.0f;      /* stationary: no extra drain */
    }

    mods->values[MOD_STREAK] = 1.0f;  /* streak modifier: placeholder, always 1.0 for now */
}

/*
 * modifier_get -- Read a single modifier value from the stack.
 *
 * Parameters:
 *   mods -- Pointer to the modifier stack (read-only).
 *   type -- Which modifier to read (enum modifier_type_t).
 *
 * Returns:
 *   The modifier value (float), or 1.0 if the type is out of range.
 *   Returning 1.0 for invalid types is a safe default because multiplying
 *   by 1.0 has no effect.
 */
float modifier_get(const modifier_stack_t *mods, modifier_type_t type) {
    if (type >= MOD_COUNT) return 1.0f;  /* out-of-bounds guard */
    return mods->values[type];
}

/*
 * stat_apply_offline_decay -- Apply catch-up decay after the device was off.
 *
 * Parameters:
 *   stats           -- Pointer to the creature's stats.
 *   elapsed_seconds -- How many real-world seconds the device was off.
 *
 * Returns: nothing
 *
 * When the device is powered off, stats don't decay in real-time. This
 * function applies a simplified "catch-up" decay when the device turns
 * back on, based on how long it was off.
 *
 * The cap at 28800 seconds (8 hours) prevents absurd stat drops if
 * someone leaves the device off for days.
 *
 * `offline_rate = 0.5f` means offline decay is half the normal rate --
 * a mercy so the creature isn't always dead when you come back.
 *
 * Energy INCREASES during offline time (assumes the creature rested).
 *
 * The (int) casts truncate the float division results to integers before
 * applying them as stat deltas.
 */
void stat_apply_offline_decay(stats_t *stats, uint32_t elapsed_seconds) {
    if (elapsed_seconds > 28800) elapsed_seconds = 28800;  /* cap at 8 hours */
    float offline_rate = 0.5f;  /* half-speed decay while offline */

    /* elapsed_seconds / 600.0f converts to "number of 10-minute periods".
     * Multiplied by offline_rate gives the stat points to subtract.
     * (int) truncates the float to integer for the stat delta. */
    stats->primary.hunger    -= (int)((elapsed_seconds / 600.0f) * offline_rate);
    stats->primary.happiness -= (int)((elapsed_seconds / 900.0f) * offline_rate);
    stats->primary.energy    += (int)(elapsed_seconds / 30.0f);   /* energy recovers */
    stats->primary.hygiene   -= (int)((elapsed_seconds / 1800.0f) * offline_rate);

    stat_clamp_all(&stats->primary);  /* ensure 0-100 range */
}

/* ─── Queries ────────────────────────────────────────────────── */

/*
 * stat_get_by_id -- Look up a primary stat value by its enum ID.
 *
 * Parameters:
 *   stats -- Pointer to the primary_stats_t (read-only).
 *   id    -- Which stat to read (STAT_HUNGER, STAT_HAPPINESS, etc.).
 *
 * Returns:
 *   The int16_t value of the requested stat, or 0 for unknown IDs.
 *
 * This function exists because sometimes we have a stat ID as a variable
 * (e.g. from a threshold_check_t) and need to read the corresponding
 * field. A switch statement is the standard C pattern for this since
 * you can't index struct fields by a variable in C (unlike array elements).
 */
int16_t stat_get_by_id(const primary_stats_t *stats, stat_id_t id) {
    switch (id) {
        case STAT_HUNGER:    return stats->hunger;
        case STAT_HAPPINESS: return stats->happiness;
        case STAT_ENERGY:    return stats->energy;
        case STAT_HYGIENE:   return stats->hygiene;
        case STAT_HEALTH:    return stats->health;
        default:             return 0;  /* unknown stat ID: safe default */
    }
}

/*
 * stat_is_critical -- Check if a specific stat is below its critical threshold.
 *
 * Parameters:
 *   stats -- Pointer to the primary_stats_t (read-only).
 *   id    -- Which stat to check.
 *
 * Returns:
 *   true if the stat is critically low, false otherwise.
 *
 * Each stat has a different critical threshold (hunger < 20, energy < 15, etc.)
 * matching the values in the thresholds[] array.
 */
bool stat_is_critical(const primary_stats_t *stats, stat_id_t id) {
    int16_t val = stat_get_by_id(stats, id);
    switch (id) {
        case STAT_HUNGER:    return val < 20;
        case STAT_HAPPINESS: return val < 20;
        case STAT_ENERGY:    return val < 15;
        case STAT_HYGIENE:   return val < 25;
        case STAT_HEALTH:    return val < 30;
        default:             return false;
    }
}

/*
 * stat_all_balanced -- Check if all primary stats are in a healthy range.
 *
 * Parameters:
 *   stats -- Pointer to the primary_stats_t (read-only).
 *
 * Returns:
 *   true if all stats are between 40 and 80 (or 40+ for health).
 *   false if any stat is outside its comfort zone.
 *
 * "Balanced" means not too low (critical) and not too high (overfed, etc.).
 * This is used to trigger the EVENT_ALL_STATS_BALANCED event and for
 * evolution calculations.
 *
 * The chained && (logical AND) short-circuits: if the first condition
 * is false, C stops evaluating the rest. This is efficient but also means
 * the function returns false as soon as any stat is out of range.
 */
bool stat_all_balanced(const primary_stats_t *stats) {
    return stats->hunger >= 40 && stats->hunger <= 80 &&
           stats->happiness >= 40 && stats->happiness <= 80 &&
           stats->energy >= 40 && stats->energy <= 80 &&
           stats->hygiene >= 40 && stats->hygiene <= 80 &&
           stats->health >= 40;
}
